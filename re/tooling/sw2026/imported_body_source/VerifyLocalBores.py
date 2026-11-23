from argparse import ArgumentParser
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import dist, fsum, isclose, nextafter, pi, tau
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(path) for path in (
    ROOT / "src", ROOT, HERE.parent, HERE.parent.parent, HERE.parent.parent / "serial",
)]

from VerifyLocalAnnulus import (
    CORPUS, D19_SHA, MANIFEST_SHA, NATIVE_BUILD, SCHEMA,
    baseline as previous_baseline, generate as previous_generation, native as observe_annulus,
    BareLabels, document, fingerprint, guard, ordered_payloads, read_owners, recipe, refuse,
)
from convert import open_document
from convert.Geometry.Parasolid import BrepTopology, DecodePartData, ParaHeaderData
from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeAnnularBody import MakeAnnularBody
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import EncodeLocalXmt
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import ReadBodyFaces
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevLoops import ReadRevLoops
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadLocalCyl import ReadLocalCyl
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.VectorSpace import SpaceVector

CASE_PINS = {
    "D19Annulus": D19_SHA,
    "D20TwoCircles": "ad42689b2b3e6e586b7acaff4c7f1c83e1839864c0877295fdd80a424aa92144",
    "D21EightCircles": "d51971d09bd449932b3bb5b18784dee3a29b7b41dec49b8a98729464f52bd5bf",
}
ANNULUS_RECEIPT = ROOT / "re/solidworks/measurements/2026/AnnularLocalImport01.json"
ANNULUS_SHA = "e84acd57394393a874f0fae93663de930809a2175ff7ad9d3cc380edbf1402d8"
FORMAT = "solidworks.sldprt"
CASES = {
    "TwinBore": (20., 13., (2., -4., -3.), (0., 0., 1.), (1., 0., 0.),
                 ((-8., 0., 3.), (8., 0., 4.)), ((2, 0, 1), (1, 2, 0))),
    "TripleBore": (22., 7.75, (-3.25, 12.5, 7.125), (0., -1., 0.), (0., 0., 1.),
                   ((-6., -4., 2.75), (5., -5., 3.), (-1., 8., 2.75)), ((3, 1, 0, 2), (0, 2, 1, 3))),
}


def xyz(value):
    return (value.x, value.y, value.z)


def close(left, right):
    if isinstance(left, (tuple, list)):
        for got, want in zip(left, right, strict=True):
            close(got, want)
    else:
        assert isclose(left, right, rel_tol=1e-12, abs_tol=1e-12), (left, right)


def face_loops(graph, face):
    return WalkXmtChain(graph, face.Integer("loop"), 15, PreviousField=None,
                        OwnerField="face", OwnerValue=face.IndexValue)


def read_active(blob):
    data = SldprtArchive.from_bytes(blob).require(KPartitionStream)
    active, *_ = DecodePartData(data, KPartitionStream)
    assert active.kind == "partition" and ParaHeaderData(active.data).schema == SCHEMA.decode()
    return active.data, ReadActiveNodes(active.data)


def observe():
    raw = (CORPUS / "Manifest.json").read_bytes()
    assert fingerprint(raw)["sha256"] == MANIFEST_SHA
    manifest = loads(raw)
    assert manifest["native_build"] == NATIVE_BUILD
    annulus = observe_annulus()
    expected = {"D20TwoCircles": 2, "D21EightCircles": 8}
    controls = {}
    rows = []
    provenance = ("re/solidworks/v2026/corpus", "re/automation/PairedCaptures")
    tracked = check_output(("git", "ls-files", "--", *provenance), cwd=ROOT, text=True)
    for relative in tracked.splitlines():
        path = Path(relative)
        if path.suffix.casefold() != ".sldprt" or any(
            part in ("heldout", "sealed") for part in relative.casefold().split("/")
        ):
            continue
        blob = (ROOT / path).read_bytes()
        active, graph = read_active(blob)
        max_loops = max((len(face_loops(graph, node)) for node in graph.values() if node.KindValue == 14), default=0)
        digest = fingerprint(blob)["sha256"]
        rows.append((relative, digest, max_loops))
        if path.stem not in expected:
            continue
        (case,) = (row for row in manifest["records"] if row["name"] == path.stem)
        assert case["split"] == "discovery" and case["sha256"] == digest == CASE_PINS[path.stem]
        bodies = tuple(node for node in graph.values() if node.KindValue == 12)
        assert len(bodies) == expected[path.stem] == case["spec"]["expected_bodies"]
        components = [component(graph, body) for body in bodies]
        rings = sorted((row["axis_origin_mm"][:2], row["radius_mm"]) for row in components)
        known = sorted((tuple(row["center_mm"]), row["radius_mm"]) for row in case["spec"]["profile"]["circles"])
        close(tuple((*point, radius) for point, radius in rings), tuple((*point, radius) for point, radius in known))
        assert max_loops == 2 and len({face for row in components for face in row["faces"]}) == 3 * len(bodies)
        controls[path.stem] = {"part": fingerprint(blob), "active": fingerprint(active), "bodies": components}
    assert len(rows) == 129 and len(controls) == 2 and not any(row[2] > 2 for row in rows)
    return {
        "native_build_of_controls": NATIVE_BUILD, "catalog": fingerprint(raw),
        "annular_cap_control": annulus, "disjoint_island_controls": controls,
        "census": {"roots": provenance, "classes": SCHEMA.decode(), "part_count": len(rows), "max_cap_loops": 2,
                   "more_than_two_loops": 0, "inventory_sha256": sha256(dumps(rows, separators=(",", ":")).encode()).hexdigest()},
    }


def component(graph, body):
    faces = WalkXmtChain(graph, graph[body.Integer("shell")].Integer("face"), 14,
                        OwnerField="shell", OwnerValue=body.Integer("shell"))
    assert len(faces) == 3
    walls = tuple(graph[graph[key].Integer("surface")] for key in faces
                  if graph[graph[key].Integer("surface")].KindValue == 51)
    (wall,) = walls
    edges = WalkXmtChain(graph, body.Integer("edge"), 16, OwnerField="owner", OwnerValue=body.IndexValue)
    assert len(edges) == 2 and sorted(len(face_loops(graph, graph[key])) for key in faces) == [1, 1, 2]
    return {"body": body.IndexValue, "faces": faces, "edges": edges,
            "axis_origin_mm": tuple(1000 * value for value in wall.FieldsValue["pvec"]),
            "radius_mm": 1000 * wall.FieldsValue["radius"]}


def cylinder(name, radius, height, centre, axis, radial):
    return BuildFullSweep(name, ((0., 0.), (radius, 0.), (radius, height), (0., height)),
                          centre, axis, radial)


def support_caps(shape):
    planes = {surface.id for surface in shape.surfaces if isinstance(surface, PlaneSurface)}
    return tuple(face for face in shape.faces if face.surface_id in planes)


def subtract_straight_bore(stock, void):
    supports = support_caps(stock)
    ends = support_caps(void)
    cap_ids = {face.id for face in ends}
    plate_planes = {row.surface_id for row in ends}
    inside_loops = {face.loop_ids[0] for face in ends}
    joined_caps = {target.id: target.loop_ids + source.loop_ids for target, source in zip(supports, ends, strict=True)}
    faces = tuple(replace(row, loop_ids=joined_caps[row.id]) if row.id in joined_caps else row for row in stock.faces)
    walls = tuple(replace(row, same_sense=False) for row in void.faces if row.id not in cap_ids)
    uses = stock.face_uses + tuple(row for row in void.face_uses if row.face_id not in cap_ids)
    return replace(stock, faces=(*faces, *walls), face_uses=uses,
                   shells=(replace(stock.shells[0], face_use_ids=tuple(row.id for row in uses)),),
                   surfaces=stock.surfaces + tuple(row for row in void.surfaces if row.id not in plate_planes),
                   curves=stock.curves + void.curves, edges=stock.edges + void.edges, vertices=stock.vertices + void.vertices,
                   loops=stock.loops + tuple(replace(row, outer=False) if row.id in inside_loops else row for row in void.loops),
                   coedges=stock.coedges + tuple(replace(row, reversed=not row.reversed) for row in void.coedges),
                   bodies=(replace(stock.bodies[0], design_body_id=""),))


def model(name, settings):
    radius, height, origin, axis, radial, bores, orders = settings
    start, normal, first = map(lambda value: SpaceVector(*value), (origin, axis, radial))
    side = CrossVector(normal, first)
    shape = cylinder(name, radius, height, start, normal, first)
    for row, (u, v, inner) in enumerate(bores, 1):
        position = OffsetVector(OffsetVector(start, first, u), side, v)
        shape = subtract_straight_bore(shape, cylinder(f"{name}-bore-{row}", inner, height, position, normal, first))
    selected = {
        face.id: tuple(face.loop_ids[index] for index in order)
        for face, order in zip(support_caps(shape), orders, strict=True)
    }
    return replace(shape, faces=tuple(replace(row, loop_ids=selected[row.id]) if row.id in selected else row for row in shape.faces))


def actual_cap(shape, face):
    topology = BrepTopology(shape)
    values = []
    for index in face.loop_ids:
        (use,) = topology.loops[index].coedge_ids
        edge = topology.edges[topology.coedges[use].edge_id]
        assert edge.start_vertex_id == edge.end_vertex_id and (edge.start_parameter, edge.end_parameter) == (0., tau)
        curve = topology.curve_by_id[edge.curve_id]
        close(xyz(topology.vertex_by_id[edge.start_vertex_id].point),
              xyz(OffsetVector(curve.center, curve.reference_direction, curve.radius)))
        values.append((xyz(curve.center), curve.radius, topology.loops[index].outer))
    return values


def verify_shape(shape, settings):
    radius, height, origin, axis, radial, bores, orders = settings
    start, normal, first = map(lambda row: SpaceVector(*row), (origin, axis, radial))
    side = CrossVector(normal, first)
    centres = [start, *(OffsetVector(OffsetVector(start, first, u), side, v) for u, v, _ in bores)]
    radii = [radius, *(row[2] for row in bores)]
    measured = tuple(actual_cap(shape, face) for face in support_caps(shape))
    assert len(measured) == 2
    moments, areas, shaft_centres = [], [], []
    for axial, order, rows in zip((0., height), orders, measured, strict=True):
        expected = [(xyz(OffsetVector(centres[index], normal, axial)), radii[index], index == 0) for index in order]
        assert [row[2] for row in rows] == [row[2] for row in expected]
        close(tuple((point, radius) for point, radius, _ in rows),
              tuple((point, radius) for point, radius, _ in expected))
        weights = [(1 if outside else -1) * pi * radius**2 for _, radius, outside in rows]
        section = fsum(weights)
        areas.append(section)
        moments.append(tuple(fsum(weight * row[0][index] for weight, row in zip(weights, rows)) / section
                             for index in range(3)))
        shaft_centres.append(next(point for point, _, outside in rows if outside))
    edges = len(shape.edges)
    span = dist(*shaft_centres)
    walls = tuple(value for value in shape.surfaces if isinstance(value, CylinderSurface))
    outside = max(value.radius for value in walls)
    side_area = tau * span * fsum(value.radius for value in walls)
    actual = (areas[0] * span, fsum(areas) + side_area, tuple((a + b) / 2 for a, b in zip(*moments)))
    section = radius**2 - fsum(r**2 for _, _, r in bores)
    local_u = -fsum(u*r*r for u, _, r in bores) / section
    local_v = -fsum(v*r*r for _, v, r in bores) / section
    centre = OffsetVector(OffsetVector(OffsetVector(start, first, local_u), side, local_v), normal, height / 2)
    close(actual, (pi*section*height, 2*pi*(section + fsum(radii)*height), xyz(centre)))
    bounds = tuple(
        tuple(sidepart(a, b) + sign * outside * (0 if axis[index] else 1)
              for index, (a, b) in enumerate(zip(*shaft_centres)))
        for sign, sidepart in ((-1, min), (1, max))
    )
    expected_ends = (origin, xyz(OffsetVector(start, normal, height)))
    close(bounds, tuple(
        tuple(sidepart(a, b) + sign * radius * (0 if axis[index] else 1)
              for index, (a, b) in enumerate(zip(*expected_ends)))
        for sign, sidepart in ((-1, min), (1, max))
    ))
    assert edges == len(shape.vertices) == 2 * len(radii)
    return {"volume_mm3": actual[0], "area_mm2": actual[1], "centroid_mm": actual[2],
            "bounds_mm": bounds, "cap_rims": measured, "derived_vertex_count": edges}


def ring_owners(nodes, count):
    body = nodes[1]
    faces = ReadBodyFaces(nodes, body, count + 2)
    caps = {}
    edge_caps = {}
    edge_walls = {}
    for index in faces:
        face = nodes[index]
        carrier = nodes[face.Integer("surface")]
        assert carrier.Integer("owner") == index
        cap = carrier.KindValue == 50
        rings, fins = ReadRevLoops(nodes, face, True, FullLoopCount=count if cap else 2)
        if cap:
            caps[index] = rings
        for fin in fins:
            edge = nodes[fin].Integer("edge")
            owners = edge_caps if cap else edge_walls
            assert edge not in owners
            owners[edge] = index
    assert len(caps) == 2 and set(edge_caps) == set(edge_walls)
    assert len({(edge_caps[key], edge_walls[key]) for key in edge_caps}) == 2 * count
    assert not any(node.KindValue in (18, 29) for node in nodes.values())
    return {"cap_loops": caps, "paired_owners": [[key, edge_caps[key], edge_walls[key]] for key in sorted(edge_caps)]}


def read_modes(blob, settings, owners):
    wall_count = len(settings[5]) + 1
    outputs, evidence = [], {}
    for mode, full in (("full", True), ("design", False)):
        value = open_document(BytesIO(blob), source_format=FORMAT, strict=True, include_brep=full,
                              include_tessellation=False, configuration="Default" if not full else None)
        (body,) = value.bodies
        (feature,) = (row for row in value.feature_timeline if row.kind is FeatureKind.IMPORTED)
        assert feature.id == body.final_feature_id == f"sldprt:feature:{owners['feature_id']}"
        assert feature.name == body.name == owners["local_group"] and body.attributes["native_object_id"] == owners["feature_id"]
        top = body.topology
        counts = (top.solid_count, top.shell_count, top.face_count, top.edge_count, top.vertex_count)
        assert counts == (1, 1, wall_count + 2, 2 * wall_count, 2 * wall_count)
        neutral = value.to_json(indent=None)
        assert CadDocument.from_json(neutral).to_json(indent=None) == neutral
        report = {"body": body.id, "feature": feature.id, "topology": counts, "json": fingerprint(neutral.encode())}
        if full:
            assert value.brep is not None and value.brep.bodies[0].design_body_id == body.id
            assert not value.brep.validate(frozenset((body.id,))) and len(value.brep_payloads) == 3
            report["geometry"] = verify_shape(value.brep, settings)
        else:
            assert value.brep is None and not value.brep_payloads
        outputs.append(value)
        evidence[mode] = report
    full, design = outputs
    assert full.feature_timeline == design.feature_timeline and full.configurations == design.configurations
    assert full.bodies[0].provenance == design.bodies[0].provenance
    return outputs, evidence


def rejected(operation, message):
    try:
        operation()
    except ValueError as error:
        assert message in str(error), str(error)
        return str(error)
    raise AssertionError("unsupported bore boundary was accepted")


def rejected_inputs():
    stock = (20., 13., (0., 0., -3.), (0., 0., 1.), (1., 0., 0.))
    orders = ((0, 1, 2), (0, 1, 2))
    almost = nextafter(14., 0.)
    assert Fraction(18.) - Fraction(4.) > Fraction(almost)
    assert Fraction(18. / 1000.) - Fraction(4. / 1000.) == Fraction(almost / 1000.)
    contrasts = {
        "overlap": (stock, ((0., 0., 4.), (5., 0., 3.)), "openings overlap or touch"),
        "touching": (stock, ((0., 0., 3.125), (6., 0., 2.875)), "openings overlap or touch"),
        "touching_exterior": (stock, ((-8., 0., 2.), (17., 0., 3.)), "does not clear the exterior"),
        "tangent_after_unit_encoding": ((18., *stock[1:]), ((-8., 0., 2.), (almost, 0., 4.)), "does not clear the exterior"),
        "oblique": ((*stock[:3], (-0.6, 0.8, 0.), (0., 0., 1.)), ((-8., 0., 2.), (8., 0., 3.)),
                    "require one signed principal axis"),
    }
    return {name: rejected(lambda: MakeAnnularBody(model(name, (*support, bores, orders))), why)
            for name, (support, bores, why) in contrasts.items()}


def changed_stations(nodes, offsets, label):
    cap = next(row for row in nodes.values() if row.KindValue == 14 and nodes[row.Integer("surface")].KindValue == 50)
    plane = nodes[cap.Integer("surface")]
    loops = face_loops(nodes, cap)
    exterior = plane.FieldsValue["pvec"]
    rings = [nodes[nodes[nodes[key].Integer("halfedge")].Integer("edge")].Integer("curve") for key in loops]
    rim = next(nodes[key] for key in rings if nodes[key].FieldsValue["centre"] != exterior)
    centre = rim.FieldsValue["centre"]
    principal = next(index for index, value in enumerate(plane.FieldsValue["normal"]) if value != 0.)
    moved = tuple(value + 0.0005 if index == principal else value for index, value in enumerate(centre))
    adjusted = replace(rim, FieldsValue=dict(rim.FieldsValue) | {"centre": moved})
    contrast = nodes | {rim.IndexValue: adjusted}
    message = "does not join its two exact cap stations"
    return {
        "off_cap_rim_read": rejected(lambda: ReadLocalCyl(contrast, offsets), message),
        "off_cap_rim_write": rejected(lambda: EncodeLocalBody(label, tuple(contrast.values())), message),
    }


def raw_tangency():
    encoded_stock, encoded_bore = 0.0065, 0.002125
    tangent = float(Fraction(encoded_stock) - Fraction(encoded_bore))
    assert Fraction(tangent) == Fraction(encoded_stock) - Fraction(encoded_bore)
    decoded = tuple(value / 0.001 for value in (encoded_stock, encoded_bore, tangent))
    for divisor in (1., 1000.):
        outer, bore, centre = map(lambda value: Fraction(value / divisor), decoded)
        assert outer - bore > centre
    settings = (6.5, 10., (0., 0., 0.), (0., 0., 1.), (1., 0., 0.),
                ((-2.5, 0., 0.5), (4.25, 0., 2.125)), ((0, 1, 2), (0, 1, 2)))
    raw = EncodeLocalXmt(MakeAnnularBody(model("TangentReprojection", settings)))
    nodes, offsets = ReadLocalNodes(raw, AllowPeriodic=True)
    replacements = {}
    for node in nodes.values():
        if node.KindValue not in (31, 51) or node.FieldsValue["radius"] != encoded_bore:
            continue
        field = "centre" if node.KindValue == 31 else "pvec"
        _, y, z = node.FieldsValue[field]
        replacements[node.IndexValue] = replace(node, FieldsValue=dict(node.FieldsValue) | {field: (tangent, y, z)})
    assert len(replacements) == 3
    changed = nodes | replacements
    message = "does not clear the exterior wall"
    return {
        "raw_exact_tangent_m": (encoded_stock, encoded_bore, tangent), "rounded_projection_mm": decoded,
        "read": rejected(lambda: ReadLocalCyl(changed, offsets), message),
        "write": rejected(lambda: EncodeLocalBody("Bore contrast", tuple(changed.values())), message),
    }


def generated_case(name, settings):
    shape = model(name, settings)
    assert not shape.validate()
    requested = document(shape)
    wall_count = len(settings[5]) + 1
    label = BareLabels(name, "Default", "Imported perforated stock")
    locator = PureWindowsPath(r"C:\KitPerforatedImport\Candidates") / (name + ".SLDPRT")
    config = recipe(label, locator, 1790000000)
    candidate = MakeBareImport(requested, config, label)
    repeat = MakeBareImport(document(model(name, settings)), config, label)
    assert candidate.BytesValue == repeat.BytesValue and candidate.StreamsValue == repeat.StreamsValue
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    assert len(archive.streams) == 12 and archive.streams == candidate.StreamsValue
    _, local, group, mark = ordered_payloads(candidate.BytesValue, archive)
    owners = read_owners(archive, group, mark)
    nodes, offsets = ReadLocalNodes(local, AllowPeriodic=True)
    assert len(nodes) == 14 * wall_count + 9 and tuple(nodes.values()) == MakeAnnularBody(shape)
    assert EncodeLocalBody(group, tuple(nodes.values())) == archive.require(KLocalBodyStream)
    readings, evidence = read_modes(candidate.BytesValue, settings, owners)
    for route in ("registry", "writer", "adapter"):
        for model_value in (requested, *readings):
            refuse(route, model_value, {})
    return {"candidate": fingerprint(candidate.BytesValue), "local_kernel": fingerprint(local),
            "streams": {key: fingerprint(value) for key, value in archive.streams.items()},
            "locator": str(locator), "written_at": 1790000000, "cells": len(nodes), "bore_count": len(settings[5]),
            "root_link": owners, "wire": ring_owners(nodes, wall_count), "sdk": evidence,
            "declined_writer_publications": 9, "owner_refusals": changed_stations(nodes, offsets, group),
            "model_geometry": verify_shape(shape, settings)}


def generate():
    with guard() as accesses:
        rows = {name: generated_case(name, settings) for name, settings in CASES.items()}
        refused = rejected_inputs()
        reprojected = raw_tangency()
    assert len({row["local_kernel"]["bytes"] for row in rows.values()}) == 2
    return {"cases": rows, "refusals": refused, "wire_tangency_contrast": reprojected,
            "runtime_input_reads": len(accesses)}


def baseline():
    data = ANNULUS_RECEIPT.read_bytes()
    assert fingerprint(data)["sha256"] == ANNULUS_SHA
    assert loads(dumps(previous_generation())) == loads(data)["model-generate"]
    checked = previous_baseline()
    return {"exact_annular_cases": 2, "annular_receipt": fingerprint(data),
            "exact_rectangle_concave_and_cylinder_cases": checked["exact_measured_controls"],
            "exact_blind_cases": checked["exact_blind_cases"], "through_cases_from_prior_chain": 2,
            "exact_logical_stream_hashes": checked["logical_stream_hashes"] + 24,
            "runtime_input_reads": 0}


def main():
    methods = {"native-observation": observe, "model-generate": generate, "baseline": baseline}
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("all", *methods))
    args = parser.parse_args()
    data = methods[args.mode]() if args.mode != "all" else {
        mode: loads(check_output((sys.executable, "-I", "-B", str(HERE), mode), timeout=60))
        for mode in methods
    } | {
        "schema": "kit.sw2026.perforated-local-import.v1", "runtime": sys.version.split()[0],
        "compressor": ZLIB_RUNTIME_VERSION, "tool": fingerprint(HERE.read_bytes()),
        "new_vendor_qualification": False, "new_heldout_cases": 0, "native_processes_started": 0,
    }
    print(dumps(data, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
