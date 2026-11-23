from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import dist, fsum, hypot, isclose
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(path) for path in (
    ROOT / "src", ROOT, HERE.parent, HERE.parent.parent, HERE.parent.parent / "serial",
)]

from BuildLocalCylinderPart import ordered_payloads, read_owners
from VerifyBareImportPackage import BareLabels, fingerprint, recipe, verify_graph
from VerifyColdImportRoundTrip import RECEIPT, check_case, guard, refuse
from VerifyLocalCylinderWrite import CASES as CYLINDERS, LIFECYCLE, MEASUREMENTS, verify_disclosed
from convert import open_document
from convert.Geometry.Parasolid import BrepTopology, BuildPartModel
from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPocket import CheckPocket
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPocket import MakeLocalPocket
from convert.adapters.solidworks.Archive.Partition.LocalPrism.OrientPocket import OrientPocket
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import ReadPrismFaces
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream
from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.Preparation.Imports.CheckImportGeo import IsOwnedPrism
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalFins import CheckLocalFins
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import MakeLocalTables
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalRoot import ReadLocalRoot
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.MakeShellBrep import JoinShellRim, ShellPrism
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource

SHELL_RECEIPT = MEASUREMENTS / "SdkColdShellCompile01.json"
SHELL_PINS = {
    "OpenShell.SLDPRT": "73a4330ef831d38273ef6128bcbff15e4a105421219293ae5454941a3c7301cd",
    "OpenShellEdited.SLDPRT": "c0be437a8c13a50c940b0d9cee51d369865abf3fa0a7ed62610fb9c76eb4b810",
}
POCKETS = {
    "Centered": ((-12.5, -9.75, 0.), (12.5, 9.75, 15.5), (-9., -6.25, 3.5), (9., 6.25, 15.5)),
    "Offset": ((-4., 9., -6.), (24., 30., 16.), (3.5, 13., 0.), (15., 25., 16.)),
}


def prism(identity, minimum, maximum):
    return ShellPrism(identity, SpaceVector(*minimum), SpaceVector(*maximum))


def pocket(name, settings):
    return JoinShellRim(prism(name + "-stock", *settings[:2]), prism(name + "-void", *settings[2:]))


def document(model):
    return CadDocument(CadSource("kit.neutral", "", ""), (Configuration("active", "Default", True),),
                       (), (), (), (), (), (), brep=model)


def vector(value):
    return (value.x, value.y, value.z)


def surface_area(model):
    ring_areas = []
    for first, *remaining in ReadMassRings(model):
        ring_areas.append(fsum(hypot(*vector(CrossVector(OffsetVector(a, first, -1.),
                                                       OffsetVector(b, first, -1.)))) / 2
                               for a, b in zip(remaining[:-1], remaining[1:], strict=True)))
    faces = {row.id: row for row in model.faces}
    loops = {row.id: row for row in model.loops}
    ordered = [loops[key] for use in model.face_uses for key in faces[use.face_id].loop_ids]
    return fsum(area if loop.outer else -area for area, loop in zip(ring_areas, ordered, strict=True))


def measures(shape, sections):
    bounds = LinearPartBox(shape)
    assert bounds is not None
    measured = ReadPartMass(shape, bounds)
    assert measured is not None
    low, high, inner_low, inner_high = sections
    outer_dims, inner_dims = (tuple(b - a for a, b in zip(start, end, strict=True))
                              for start, end in ((low, high), (inner_low, inner_high)))
    width, breadth, height = outer_dims
    inner_width, inner_breadth, cavity_depth = inner_dims
    outer = width * breadth * height
    cavity = inner_width * inner_breadth * cavity_depth
    volume = outer - cavity
    area = 2 * (width * breadth + (width + breadth) * height + (inner_width + inner_breadth) * cavity_depth)
    centroid = tuple((outer * (a + b) - cavity * (c + d)) / (2 * volume)
                     for a, b, c, d in zip(low, high, inner_low, inner_high, strict=True))
    observed = (measured.Volume, surface_area(shape), *measured.Centroid)
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
               for a, b in zip(observed, (volume, area, *centroid), strict=True)), (observed, volume, area, centroid)
    assert dist(vector(bounds.minimum), low) < 1e-12 and dist(vector(bounds.maximum), high) < 1e-12
    return {"volume_mm3": observed[0], "area_mm2": observed[1], "centroid_mm": measured.Centroid}


def rim(nodes):
    faces = tuple(node for node in nodes.values() if node.KindValue == 14)
    groups = {node.IndexValue: WalkXmtChain(nodes, node.Integer("loop"), 15, PreviousField=None,
                                           OwnerField="face", OwnerValue=node.IndexValue) for node in faces}
    assert sorted(map(len, groups.values())) == [1] * 10 + [2]
    assert len({index for group in groups.values() for index in group}) == 12
    face, = (key for key, group in groups.items() if len(group) == 2)
    loops = groups[face]
    areas = []
    for index in loops:
        current = head = nodes[index].Integer("halfedge")
        points = []
        for _ in range(4):
            fin = RequireXmt(nodes, current, 17)
            assert fin.Integer("loop") == index
            vertex = RequireXmt(nodes, fin.Integer("vertex"), 18)
            points.append(RequireXmt(nodes, vertex.Integer("point"), 29).FieldsValue["pvec"])
            current = fin.Integer("forward")
        assert current == head and len(set(points)) == 4 and len({point[2] for point in points}) == 1
        areas.append(fsum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1])) * 5e5)
    assert areas[0] > -areas[1] > 0
    face_node = nodes[face]
    plane = nodes[face_node.Integer("surface")]
    assert plane.Integer("owner") == face
    sense = -1 if face_node.String("sense") == "-" else 1
    assert tuple(sense * value for value in plane.FieldsValue["normal"]) == (0., 0., 1.)
    return {"face": face, "loop_ids": loops, "signed_xy_area_mm2": areas,
            "surface_face_sense": face_node.String("sense"), "plane_normal": plane.FieldsValue["normal"]}


def native(folder):
    receipt_raw = SHELL_RECEIPT.read_bytes()
    previous = loads(receipt_raw)["saved"]["cases"]
    observed = {}
    for name, pin in SHELL_PINS.items():
        source = (folder / name).read_bytes()
        assert sha256(source).hexdigest() == previous[name]["sha256"] == pin
        doc = open_document(source, source_format="solidworks.sldprt", strict=True, include_brep=True)
        active, = (row for row in doc.brep_payloads if row.source_stream == KPartitionStream and row.kind == "partition")
        graph = ReadActiveNodes(active.data)
        assert doc.brep is not None and counts(doc.brep) == (11, 12, 24, 48, 16)
        owner, = (row for row in graph.values() if row.KindValue == 12 and row.Integer("edge"))
        observed[name] = {"whole": fingerprint(source), "active_partition": fingerprint(active.data),
                          "rim": rim(graph), "body_node": owner.IndexValue, "topology": counts(doc.brep)}
    return {"observations": observed, "native_identity_authority": fingerprint(receipt_raw)}


def counts(model):
    return tuple(len(values) for values in (model.faces, model.loops, model.edges, model.coedges, model.vertices))


def rejected(operation, diagnostic):
    try:
        operation()
    except ValueError as error:
        assert diagnostic in str(error), str(error)
        return str(error)
    raise AssertionError("an unsupported pocket reached the next phase")


def read_back(result, model):
    archive = SldprtArchive.from_bytes(result.BytesValue)
    assert archive.streams == result.StreamsValue and len(archive.streams) == 12
    _, raw, group, mark = ordered_payloads(result.BytesValue, archive)
    owners = read_owners(archive, group, mark)
    nodes, offsets = ReadLocalNodes(raw)
    ReadLocalRoot(nodes, False)
    for row in nodes.values():
        if row.KindValue == 17:
            CheckLocalFins(nodes, row)
    assert tuple(nodes.values()) == MakeLocalPocket(model)
    assert tuple(nodes.values()) == MakeLocalPocket(OrientPocket(model))
    assert EncodeLocalBody(group, tuple(nodes.values()), AllowPocket=True) == archive.require(KLocalBodyStream)
    observed_rim = rim(nodes)
    inner = nodes[observed_rim["loop_ids"][1]]
    foreign = next(node.IndexValue for node in nodes.values() if node.KindValue == 14 and node.IndexValue != observed_rim["face"])
    altered = tuple(replace(node, FieldsValue=dict(node.FieldsValue) | {"face": foreign}) if node is inner else node
                    for node in nodes.values())
    observed_rim["foreign_loop_owner_refusal"] = rejected(
        lambda: EncodeLocalBody(group, altered, AllowPocket=True), "owner chain is not reciprocal",
    )
    restored = BuildPartModel(MakeLocalTables(nodes, offsets))
    assert counts(restored) == (11, 12, 24, 48, 16)
    assert len(restored.bodies) == len(restored.shells) == len(restored.regions) == 1
    assert restored.shells[0].closed and restored.regions[0].solid and not restored.validate()
    topology = BrepTopology(restored)
    CheckPocket(restored, topology, ReadPrismFaces(restored, topology, AllowPocket=True))
    return raw, restored, owners, observed_rim


def generated_case(name, sections):
    model = pocket(name, sections)
    doc = document(model)
    labels = BareLabels(name, "Default", "Imported pocket")
    target = PureWindowsPath(r"C:\KitPocketTopology\Candidates") / (name + ".SLDPRT")
    settings = recipe(labels, target, 1790000000)
    result = MakeBareImport(doc, settings, labels)
    verify_graph(result, labels)
    repeat = MakeBareImport(document(pocket(name, sections)), settings, labels)
    assert repeat.BytesValue == result.BytesValue and repeat.StreamsValue == result.StreamsValue
    raw, restored, owners, rim_owner = read_back(result, model)
    plain = prism(name + "-stock", *sections[:2])
    stock, = plain.bodies
    rectangle = replace(plain, bodies=(replace(stock, design_body_id=""),))
    reference = MakeBareImport(document(rectangle), settings, labels)
    assert set(reference.StreamsValue) == set(result.StreamsValue)
    assert [key for key in reference.StreamsValue if reference.StreamsValue[key] != result.StreamsValue[key]] == [KLocalBodyStream]
    assert len(reference.StreamsValue[KLocalBodyStream]) < len(result.StreamsValue[KLocalBodyStream])
    refusal = rejected(lambda: open_document(result.BytesValue, source_format="solidworks.sldprt",
                                            strict=True, include_brep=True), "single-loop profile")
    for route in ("registry", "writer", "adapter"):
        refuse(route, doc, {})
    rejected(lambda: IsOwnedPrism(OrientPocket(model)), "cylinder requires its solid mantle")
    attributes = rejected(lambda: MakeBareImport(doc, settings, labels, OwnedBody=True),
                          "does not admit attributed body owners")
    return {"part": fingerprint(result.BytesValue), "streams": {key: fingerprint(value) for key, value in result.StreamsValue.items()},
            "local_xmt": fingerprint(raw), "whole_deterministic": True, "logical_streams": 12,
            "outward_representation_exact": True,
            "source_geometry": measures(model, sections), "read_geometry": measures(restored, sections),
            "physical_rim": rim_owner, "archive_owners": owners, "topology": counts(restored),
            "same_locator_box_local_bytes": len(reference.StreamsValue[KLocalBodyStream]),
            "strict_public_read_refusal": refusal, "public_write_refusals": 3,
            "unmeasured_attribution_refusal": attributes, "resident_nodes": len(MakeLocalPocket(model)),
            "explicit_neutral_extents_mm": sections, "logical_destination": str(target), "written_at": 1790000000}


def negatives():
    sections = POCKETS["Offset"]
    model = pocket("negative", sections)
    loop, *others = model.loops
    plane, *planes = model.surfaces
    wrong_plane = replace(plane, origin=SpaceVector(plane.origin.x, plane.origin.y, plane.origin.z + 1e-10))
    touch = ((sections[0][0], *sections[2][1:]), sections[3])
    through = ((*sections[2][:2], sections[0][2]), sections[3])
    return {name: rejected(lambda: MakeLocalPocket(candidate), diagnostic) for name, candidate, diagnostic in (
        ("wrong_plane_station", replace(model, surfaces=(wrong_plane, *planes)), "exact plane station"),
        ("outer_flag_removed", replace(model, loops=(replace(loop, outer=False), *others)), "ordered planar trims"),
        ("attribute_present", replace(model, loops=(replace(loop, attributes={"color": "blue"}), *others)), "attributes or provenance"),
        ("touches_exterior", pocket("touch", (*sections[:2], *touch)), "inside the outer rim"),
        ("passes_through_floor", pocket("through", (*sections[:2], *through)), "inside the outer rim"),
    )}


def prepare():
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "cp1252"):
        lookup(codec)
    import_module("interchange.document.Models.DocumentWalk")


def generate():
    prepare()
    with guard() as events:
        cases = {name: generated_case(name, sections) for name, sections in POCKETS.items()}
        refusals = negatives()
    return {"cases": cases, "neutral_refusals": refusals, "runtime_input_reads": len(events)}


def controls():
    prepare()
    planar = loads(RECEIPT.read_bytes())
    box = {key: check_case(key, planar) for key in ("RectangularBare", "ConcaveOwned")}
    cylinder_raw = (MEASUREMENTS / LIFECYCLE).read_bytes()
    cylinder = loads(cylinder_raw)
    assert cylinder["controls_healthy"] and cylinder["disclosed_native_part_lifecycles"] == 2
    with guard() as events:
        curves = {key: verify_disclosed(key, value, cylinder["cases"][key])[0] for key, value in CYLINDERS.items()}
    periodic = {key: {"part": value["part"], "logical_streams": len(value["streams"]),
                      "local_kernel": value["local_kernel"], "geometry": value["measured"]}
                for key, value in curves.items()}
    return {"planar": box, "periodic": periodic, "runtime_input_reads": len(events),
            "periodic_authority": fingerprint(cylinder_raw), "planar_authority": fingerprint(RECEIPT.read_bytes())}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("all", "generate", "native", "controls"))
    parser.add_argument("--disclosed-native-directory", type=Path)
    args = parser.parse_args()
    if args.mode in ("all", "native") and args.disclosed_native_directory is None:
        parser.error("the pinned disclosed directory is required for native observations")
    modes = {"generate": generate, "native": lambda: native(args.disclosed_native_directory), "controls": controls}
    if args.mode != "all":
        result = modes[args.mode]()
    else:
        result = {name: loads(check_output((sys.executable, "-I", "-B", str(HERE), name,
                                           "--disclosed-native-directory", str(args.disclosed_native_directory)), timeout=60))
                  for name in modes}
        result |= {"schema": "kit.sw2026.local-pocket-offline.v1", "compressor": ZLIB_RUNTIME_VERSION,
                   "runtime": sys.version.split()[0], "probe_sha256": fingerprint(HERE.read_bytes())["sha256"],
                   "native_processes_started": 0, "new_heldout_cases": 0, "public_writer_admitted": False}
    print(dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
