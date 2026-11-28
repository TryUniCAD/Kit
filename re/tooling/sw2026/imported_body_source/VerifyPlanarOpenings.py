from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import dist, isclose
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyLocalPocket import (
    ROOT, BareLabels, CadDocument, MakeBareImport, counts, document, fingerprint,
    guard, ordered_payloads, prepare, prism, read_owners, recipe, refuse, rejected,
    surface_area, vector,
)
from VerifyLocalPocketRead import activity_contrasts, controls, generated as blind_read
from ObservePlanarOpening import area_and_rings, cap_chains, observe
from convert import open_document
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPocket import MakeLocalPocket
from convert.adapters.solidworks.Archive.Partition.LocalPrism.OrientPocket import OrientPocket
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.VectorSpace import SpaceVector

CASES = {
    "CenteredPassage": (((-20., -11., -3.5), (20., 11., 14.5)), ((-8., -4.5, -3.5), (8., 4.5, 14.5)), True),
    "OffsetPassage": (((5., -22., -17.), (37., 6., 5.)), ((12., -20., -17.), (25., -6., 5.)), False),
}
PRIOR_RECEIPT = ROOT / "re/solidworks/measurements/2026/SdkLocalPocketRead01.json"
PRIOR_SHA = "18f813c67561bbe21c195c6456297ac743afe6ccdbe9156e09ea3b1f97aae019"
COUNTS = (10, 12, 24, 48, 16)
FORMAT = "solidworks.sldprt"


def join_passage(stock, passage, hole_first):
    inside_caps = passage.faces[:2]
    rim_ids = {face.loop_ids[0] for face in inside_caps}
    planes = {face.surface_id for face in inside_caps}
    reversed_fins = {key for loop in passage.loops if loop.id in rim_ids for key in loop.coedge_ids}
    caps = tuple(replace(outside, loop_ids=(*inside.loop_ids, *outside.loop_ids) if hole_first
                         else (*outside.loop_ids, *inside.loop_ids))
                 for outside, inside in zip(stock.faces[:2], inside_caps, strict=True))
    uses = stock.face_uses + tuple(replace(use, reversed=True) for use in passage.face_uses[2:])
    return replace(
        stock,
        curves=stock.curves + passage.curves,
        surfaces=stock.surfaces + tuple(surface for surface in passage.surfaces if surface.id not in planes),
        vertices=stock.vertices + passage.vertices,
        edges=stock.edges + passage.edges,
        loops=stock.loops + tuple(replace(loop, coedge_ids=loop.coedge_ids[::-1], outer=False)
                                  if loop.id in rim_ids else loop for loop in passage.loops),
        coedges=stock.coedges + tuple(replace(fin, reversed=not fin.reversed)
                                      if fin.id in reversed_fins else fin for fin in passage.coedges),
        faces=caps + stock.faces[2:] + passage.faces[2:],
        face_uses=uses,
        shells=(replace(stock.shells[0], face_use_ids=tuple(use.id for use in uses)),),
        bodies=(replace(stock.bodies[0], design_body_id=""),),
    )


def geometry(name, outer, inner, hole_first):
    return join_passage(prism(name + "-stock", *outer), prism(name + "-opening", *inner), hole_first)


def measured(value, outer, inner):
    outer_min, outer_max = outer
    inner_min, inner_max = inner
    dx, dy, height = (b - a for a, b in zip(outer_min, outer_max, strict=True))
    hole_x, hole_y, hole_height = (b - a for a, b in zip(inner_min, inner_max, strict=True))
    assert height == hole_height and outer_min[2] == inner_min[2]
    stock, hole = dx * dy, hole_x * hole_y
    expected_volume = (stock - hole) * height
    expected_area = 2 * (stock - hole) + 2 * (dx + dy + hole_x + hole_y) * height
    expected_center = tuple((stock * (a + b) - hole * (c + d)) / (2 * (stock - hole))
                            for a, b, c, d in zip(outer_min, outer_max, inner_min, inner_max, strict=True))
    extent = LinearPartBox(value)
    assert extent is not None and dist(vector(extent.minimum), outer_min) < 1e-12
    assert dist(vector(extent.maximum), outer_max) < 1e-12
    mass = ReadPartMass(value, extent)
    assert mass is not None
    area = surface_area(value)
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(
        (mass.Volume, area, *mass.Centroid), (expected_volume, expected_area, *expected_center), strict=True,
    ))
    return {"volume_mm3": mass.Volume, "area_mm2": area, "center_mm": mass.Centroid,
            "bounds_mm": (vector(extent.minimum), vector(extent.maximum))}


def read_modes(source, owner, sections, expected_order):
    documents, evidence = [], {}
    for mode, full in (("full", True), ("design", False)):
        created = open_document(BytesIO(source), source_format=FORMAT, strict=True, include_brep=full,
                                include_tessellation=False, configuration=None if full else "Default")
        body, = created.bodies
        feature, = (step for step in created.feature_timeline if step.kind is FeatureKind.IMPORTED)
        assert body.name == feature.name == owner["local_group"]
        assert body.final_feature_id == feature.id == f"sldprt:feature:{owner['feature_id']}"
        assert body.attributes["native_object_id"] == owner["feature_id"]
        topo = body.topology
        summary = (topo.solid_count, topo.shell_count, topo.face_count, topo.edge_count, topo.vertex_count)
        assert summary == (1, 1, 10, 24, 16)
        neutral = created.to_json(indent=None)
        restored = CadDocument.from_json(neutral)
        assert neutral == restored.to_json(indent=None)
        result = {"feature": feature.id, "topology": summary, "json_sha256": sha256(neutral.encode()).hexdigest()}
        if full:
            assert created.brep is not None and counts(created.brep) == COUNTS
            assert created.brep.bodies[0].design_body_id == body.id and len(created.brep_payloads) == 3
            roles = {value.id: value.outer for value in created.brep.loops}
            cap_orders = [tuple(roles[key] for key in face.loop_ids) for face in created.brep.faces if len(face.loop_ids) > 1]
            assert cap_orders == [expected_order] * 2 and not created.brep.validate(frozenset((body.id,)))
            result |= {"cap_roles": cap_orders, "geometry": measured(created.brep, *sections)}
        else:
            assert created.brep is None and not created.brep_payloads
        documents.append(created)
        evidence[mode] = result
    full, design = documents
    assert full.feature_timeline == design.feature_timeline and full.configurations == design.configurations
    assert full.bodies[0].provenance == design.bodies[0].provenance
    return documents, evidence


def model_proof(name, values):
    outer, inner, hole_first = values
    boundary = geometry(name, *values)
    assert counts(boundary) == COUNTS and not boundary.validate()
    requested = document(boundary)
    locator = PureWindowsPath(r"C:\KitPlanarOpenings\Candidates") / (name + ".SLDPRT")
    labels = BareLabels(name, "Default", "Imported passage")
    options = recipe(labels, locator, 1790000000)
    result = MakeBareImport(requested, options, labels)
    repeat = MakeBareImport(document(geometry(name, *values)), options, labels)
    assert result.BytesValue == repeat.BytesValue and result.StreamsValue == repeat.StreamsValue
    archive = SldprtArchive.from_bytes(result.BytesValue)
    assert len(archive.streams) == 12 and archive.streams == result.StreamsValue
    _, raw, group, mark = ordered_payloads(result.BytesValue, archive)
    owner = read_owners(archive, group, mark)
    nodes, _ = ReadLocalNodes(raw)
    assert len(nodes) == 165 and tuple(nodes.values()) == MakeLocalPocket(OrientPocket(boundary))
    assert EncodeLocalBody(group, tuple(nodes.values()), AllowPocket=True) == archive.require(KLocalBodyStream)
    capped = cap_chains(nodes)
    expect = (False, True) if hole_first else (True, False)
    cap_stats = []
    for height, face, links, direction, *_ in capped:
        areas = [area_and_rings(nodes, nodes[key], False)[0] for key in links]
        assert tuple(direction * area > 0 for area in areas) == expect
        cap_stats.append({"face": face, "loops": links, "height_mm": height * 1000,
                          "effective_normal": direction, "signed_xy_area_mm2": areas})
    documents, report = read_modes(result.BytesValue, owner, (outer, inner), expect)
    for route in ("registry", "writer", "adapter"):
        for value in (requested, *documents):
            refuse(route, value, {})
    test_rim = cap_stats[1]
    refusals = activity_contrasts(result, boundary, group, {"face": test_rim["face"], "loop_ids": test_rim["loops"]})
    return {
        "part": fingerprint(result.BytesValue), "raw_kernel": fingerprint(raw),
        "streams": {key: fingerprint(value) for key, value in archive.streams.items()},
        "locator": str(locator), "written_at": 1790000000, "neutral_bounds_mm": (outer, inner),
        "typed_archive_owners": owner, "deterministic_local_cells": len(nodes), "physical_caps": cap_stats,
        "source_metrics": measured(boundary, outer, inner), "sdk": report,
        "refusals": refusals, "public_write_refusals": 9,
    }


def outside_profile():
    outer, inner, _ = CASES["CenteredPassage"]
    first = geometry("OneHole", outer, inner, True)
    distinct_bore = prism("SecondHole", (12., -8., -3.5), (17., 1., 14.5))
    twin = join_passage(first, distinct_bore, False)
    assert not twin.validate() and counts(twin) == (14, 18, 36, 72, 24)
    touch = geometry("WallTouch", outer, ((-20., -4.5, -3.5), inner[1]), False)
    rim = next(face for face in first.faces if len(face.loop_ids) == 2)
    outside_loop = next(loop for loop in first.loops if loop.id in rim.loop_ids and loop.outer)
    rules = replace(first, loops=tuple(replace(loop, outer=False) if loop is outside_loop else loop for loop in first.loops))
    plane = next(plane for plane in first.surfaces if plane.id == rim.surface_id)
    pvec = plane.origin
    out_plane = replace(first, surfaces=tuple(replace(value, origin=SpaceVector(pvec.x, pvec.y, pvec.z + 1e-10))
                                             if value is plane else value for value in first.surfaces))
    return {
        "two_disjoint_through_openings": rejected(lambda: MakeLocalPocket(twin), "one ordered outer loop"),
        "opening_touches_stock": rejected(lambda: MakeLocalPocket(touch), "inside the outer rim"),
        "false_exterior_role": rejected(lambda: MakeLocalPocket(rules), "ordered planar trims"),
        "wrong_carrier_station": rejected(lambda: MakeLocalPocket(out_plane), "exact plane station"),
    }


def generated():
    prepare()
    with guard() as events:
        cases = {name: model_proof(name, info) for name, info in CASES.items()}
        refused = outside_profile()
    assert len({result["part"]["sha256"] for result in cases.values()}) == len(cases)
    return {"cases": cases, "neutral_refusals": refused, "runtime_input_reads": len(events)}


def baseline():
    data = PRIOR_RECEIPT.read_bytes()
    assert sha256(data).hexdigest() == PRIOR_SHA
    prior = loads(data)
    assert loads(dumps(blind_read())) == prior["generated"]
    assert loads(dumps(controls())) == prior["controls"]
    return {"previous_receipt": fingerprint(data), "exact_blind_cases": 2, "exact_measured_controls": 4,
            "blind_strict_read_and_json_exact": True, "logical_stream_hashes": 72, "runtime_input_reads": 0}


def main():
    parser = ArgumentParser()
    methods = {"observe": observe, "generate": generated, "baseline": baseline}
    parser.add_argument("mode", choices=("all", *methods))
    args = parser.parse_args()
    if args.mode == "all":
        result = {mode: loads(check_output((sys.executable, "-I", "-B", str(HERE), mode), timeout=60))
                  for mode in methods}
        result |= {"schema": "kit.sw2026.planar-import-openings.v1",
                   "input_programs": {path.name: fingerprint(path.read_bytes()) for path in
                                      (HERE, HERE.with_name("ObservePlanarOpening.py"))},
                   "runtime": sys.version.split()[0], "compressor": ZLIB_RUNTIME_VERSION,
                   "native_processes_started": 0, "new_heldout_cases": 0, "new_public_writer_admission": False}
    else:
        result = methods[args.mode]()
    print(dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
