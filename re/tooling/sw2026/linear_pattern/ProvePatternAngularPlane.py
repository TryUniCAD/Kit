from argparse import ArgumentParser
from math import cos, dist, hypot, radians, sin
from pathlib import Path
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from CheckPatternAngleOwners import check_angles, node_fields, point, require, roots_of_kind
from PatternAngleGeometry import WITNESS_RADIUS
from PatternAngleWire import ANGLE_PLANE, read_resolved, write_resolved
from PatternEnvelopeSpec import specification
from ProvePatternAngleOwners import PROVEN_HINGE, exact_config
from ProvePatternAngleArc import SOURCE_OWNERS, ANNOTATION, span_report
from ProvePatternPlaneDirectionRule import Image, MEASUREMENTS, MODULES, checked, digest, document_rows, encode, module
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase


PRIOR_EVIDENCE = {
    "LocalLinearPatternFiniteHinge01.json": PROVEN_HINGE,
    "LocalLinearPatternHingeAxisGraph01.json": "e37b9369c5f5e6391444b28a8f6a988fdb338980762cbe31993dff9b6483b6e3",
    "LocalLinearPatternAngularDatumOwners01.json": SOURCE_OWNERS,
    "LocalLinearPatternAnnotationCatalog01.json": ANNOTATION,
    "LocalLinearPatternAngularArc01.json": "7a696419144538fb6e876e568d633ce9f05a8cc3d57c0bcacf06ce7204e2f2f0",
}
SPANS = {
    "constrained_plane_init": (0x4B8ED160, 0x4B8ED241, "bb9b4966dabeee4e2365012ec031f8b36ac775a7a623dd75b2e515eb23b26ffb"),
    "plane_owner_constructor": (0x4C2D2D20, 0x4C2D2DDC, "d772f13c562309b6048d0e3c33a8457e6a37dbc171596039f5065d217f460ee4"),
    "owner_taking_plane_data": (0x4C2DADB0, 0x4C2DAF8C, "d845c051d198ee9a40a60087ddd86a705afd16069d46c0f0cdba9d9034a244b7"),
    "angle_dimension_factory": (0x4C820D30, 0x4C820E09, "33645bac0b9e5413e63474db85159920c410cc792ac4271bf82deafb5f722d56"),
    "parameter_name_ordinal": (0x4C820F20, 0x4C820FA8, "ea388ce9e1011ab700de0337e756a58cfe8218510444cc1f3e676e9c97923be5"),
    "angle_parameter_factory": (0x4C821470, 0x4C8214AB, "591c2e427f35be3c45698384d00fe087f0bd84c80f7980176339425ff566f260"),
    "dimension_persistent_registration": (0x4C821C40, 0x4C821D69, "0e415a01819436714d3a891db3df28dc48fa5e99d3f7f110122343bb99f7d1dc"),
    "component_axis_reference": (0x4B278B80, 0x4B278C13, "b79df13c1ea0e868baa116d09c103c5e4b083cffd8be21ca58316e93e1c2cc3a"),
    "set_foreshorten_shifted_point": (0x4C896990, 0x4C8969E0, "89aad7a2dd555132eb58641bf267ef129cb84d4d29e18a7bb089faaee8c92fac"),
    "store_leader_index": (0x4C82E7EF, 0x4C82E7FE, "2d99f74eddc664e7f061a0438ca3a20d58667557702f1a0e0c2cffc8f3a5f4f6"),
    "store_ordinary_shifted_point": (0x4C82E87A, 0x4C82E88A, "090e9267314e8843af45c077526e8b01d16f2367ab661c2ab4b1e8a8aa0d2bd9"),
    "load_leader_and_shift": (0x4C830BD4, 0x4C830BF4, "6d2c022c87fd0fba8abc4ca098925f32d971e214f1521aef1bb7de3eb4389ad9"),
}


def static_owners(directory):
    image = Image(directory / "sldmodu.dll")
    identified = module(image, MODULES[image.path.name])
    expected = {"write_long": (0x4CD3D880, "swccu.dll", "??6su_CArchive@@QEAAAEAV0@J@Z"),
                "read_long": (0x4CD3D888, "swccu.dll", "??5su_CArchive@@QEAAAEAV0@AEAJ@Z"),
                "write_point": (0x4CD3A948, "sldmgu.dll", "??6@YAAEAVsu_CArchive@@AEAV0@AEAVmgPoint_c@@@Z"),
                "read_point": (0x4CD3A940, "sldmgu.dll", "??5@YAAEAVsu_CArchive@@AEAV0@AEAVmgPoint_c@@@Z")}
    imports = {}
    for role, (address, library, function) in expected.items():
        entry = image.imports[address]
        require(entry == {"module": library, "symbol": function}, "current display style archive overload changed")
        imports[role] = {"address": hex(address), **entry}
    return {"module": identified, "spans": span_report(image, SPANS), "actual_style_archive_imports": imports}


def disclosed(share, earlier):
    hinge = earlier["LocalLinearPatternFiniteHinge01.json"]
    previous = earlier["LocalLinearPatternAngularDatumOwners01.json"]["disclosed_cases"]
    ends = {name: tuple(map(tuple, case["from_authored_boxes"]["ordered_endpoints_m"]))
            for case in hinge["disclosed_cases"].values() for name in case["typed_saves"]}
    angle = specification()["direction_datum"]["arguments"][1]
    cases = {}
    for path, pin, row in document_rows(share):
        if row["plane_data_class"] != ANGLE_PLANE:
            continue
        base = previous[path.name]
        require(base["sha256"] == pin, "disclosed angular owner is outside the measured source set")
        archive, headers, config, config_bytes = exact_config(path, pin)
        scope = MakeLinkContext(config, ReadCmgrMut(archive.require("Contents/CMgr"), 19000))
        raw = archive.require("Contents/Config-0-ResolvedFeatures")
        roots, extra, initial_map = read_resolved(raw, config.MapValue, scope, source_replay=True)
        replay, replay_map = write_resolved(roots, extra, config.MapValue, scope, source_replay=True)
        counters = [config.MapValue.CounterValue, replay_map.CounterValue]
        require(replay == raw and initial_map == replay_map and counters == base["map_counters"] and len(roots) == base["root_count"],
                "disclosed angular graph changed exact class/stream framing")
        observed = check_angles(config.RootValue, roots, headers, ends[path.name], angle)
        hinge_id = observed["selected_ids"]["hinge"]
        plane_id = observed["feature"]["id"]
        (actual_plane,) = [node for node in roots_of_kind(roots, "moRefPlane_c") if node.FieldsValue["f08"] == plane_id]
        data = node_fields(actual_plane.FieldsValue["f6f8"], ANGLE_PLANE)
        display = node_fields(data["f150"], "moDisplayAngularDim_c")
        dim = node_fields(node_fields(display["f850"][0]["o"], "moFeatureDimHandle_c")["ff0"], "AngleDim_c")
        parameter = node_fields(dim["f28"], "moAngleParameter_c")
        next_ids = [header.FieldsValue["f08"] for header in headers]
        use_id = dim["f50"]
        require(hinge_id < use_id < plane_id < next_ids[0] == next_ids[1] and parameter["f08"] == -1
                and point(display["ff68"]) == (0.0, 0.0, 0.0),
                "native dimension/plane ordering, unregistered parameter or scoped style changed")
        cases[path.name] = {"sha256": pin, "linked_stream_hashes": [digest(config_bytes), digest(raw)],
                            "map_counters": counters, "root_count": len(roots), "actual_driver": observed["driver"],
                            "stored_leader_index": display["ff80"], "stored_shift_m": point(display["ff68"]),
                            "hinge_dimension_plane_ids": [hinge_id, use_id, plane_id],
                            "matching_hinge_creation_times": [DatumTime(header, hinge_id) for header in headers],
                            "matching_plane_creation_times": [DatumTime(header, plane_id) for header in headers]}
    require(len(cases) == 4 and len({row["stored_leader_index"] for row in cases.values()}) == 2,
            "expected four earlier disclosed angular files with different saved leader indices")
    return cases


def model_case(name, width, height, deep, degrees, order, epoch, leader):
    axes = {"*Top": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
            "*Front": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            "*Back": ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))}
    angle = radians(degrees)
    vertices = ((0.0, 0.0), (width, 0.0), (width, height), (0.0, height))
    depth = 18.625 if deep else 12.75
    request = {"model": {"document": MakePolygonCase(name, vertices, deep)["document"],
                         "path": f"C:\\KitAngularDatumGraph\\{name}.SLDPRT", "epoch": epoch,
                         "axis_name": name + " hinge",
                         "plane": {"name": name + " angled datum", "angle_rad": angle, "reverse": False,
                                   "annotation_view": "*Back", "design_intent": bool(leader),
                                   "selected_leader": leader, "shifted_point_m": (0.0, 0.0, 0.0)},
                         "views": [{"name": view, "basis": axes[view]} for view in order],
                         "active": None, "shown": [None]},
               "contrast_leader": 1 - leader}
    neutral = encode(request)
    command = (sys.executable, "-I", "-B", str(HERE.with_name("PatternAngularPlaneProcess.py")))
    first, second = (run(command, input=neutral, capture_output=True, cwd=ROOT, timeout=30) for _ in range(2))
    for status in (first, second):
        require(status.returncode == 0, "guarded angular graph rejected its authored request\n" + status.stderr.decode())
    require(not first.stderr and not second.stderr and first.stdout == second.stdout, "neutral angular plane output is not deterministic")
    result = json.loads(first.stdout)
    physical_depth = depth * 0.001
    centre = (0.55 * physical_depth * sin(angle), 0.55 * physical_depth * cos(angle), 0.5 * physical_depth)
    expected_normal = (cos(angle), -sin(angle), 0.0)
    expected_radius = hypot(centre[0] - WITNESS_RADIUS * sin(angle * 0.5), WITNESS_RADIUS * cos(angle * 0.5) - centre[1])
    prediction = result["observed"]["geometry_prediction"]
    require(dist(result["standalone_plate_size_m"], (width * 0.001, height * 0.001, physical_depth)) < 1e-16
            and dist(centre, prediction["witness_points_m"][2]) < 1e-16
            and dist(expected_normal, prediction["basis_u_v_n"][2]) < 2e-15 and abs(expected_radius - prediction["label_radius_m"]) < 1e-16
            and result["observed"]["driver"]["annotation_view_id"] == 200 + order.index("*Back")
            and result["observed"]["driver"]["angle_rad"] == angle and result["fresh_owner_aliases"]
            and result["root_count"] == 21 and result["preserved_prior_root_count"] == 20
            and result["guarded_runtime_reads"] == 0 and result["cad_files_written"] == 0
            and len(result["bad_inputs"]) == 6 and len(result["bad_readback_owners"]) == 5,
            "guarded angular graph disagrees with independently authored plate, dimension, view or style")
    return {"request_sha256": digest(neutral), "authored_dimensions_mm": [width, height, depth], "authored_angle_degrees": degrees,
            "independent_centre_m": centre, "independent_normal": expected_normal, "independent_label_radius_m": expected_radius, **result}


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    earlier = {name: json.loads(checked(MEASUREMENTS / name, pin)) for name, pin in PRIOR_EVIDENCE.items()}
    variants = (
        ("ArcGraphAlpha", 137.5, 88.5, True, 28.625, ("*Back", "*Top"), 1795092001, 0),
        ("ArcGraphBeta", 121.125, 73.375, False, 61.875, ("*Top", "*Front", "*Back"), 1795092061, 1),
    )
    models = [model_case(*variant) for variant in variants]
    require(models[0]["streams"]["Config-0-ResolvedFeatures"]["bytes"] != models[1]["streams"]["Config-0-ResolvedFeatures"]["bytes"]
            and models[0]["map_counters"][0] != models[1]["map_counters"][0],
            "authored model and catalog variations did not change linked framing")
    report = {"schema": "kit.sw2026.research-only.angular-plane-graph.v1", "previous_receipts": PRIOR_EVIDENCE,
              "static_owner_boundaries": static_owners(args.binaries), "generated_models": models,
              "disclosed_replays": disclosed(args.disclosed_share, earlier), "guarded_processes": 4, "independent_graphs_built": 8,
              "native_calls": 0, "heldout_accesses": 0, "cad_files_written": 0, "pattern_seed_built": False,
              "tools": {name: digest(HERE.with_name(name).read_bytes()) for name in (
                  HERE.name, "MakePatternAngularPlane.py", "PatternAngularPlaneProcess.py", "PatternAngleWire.py",
                  "MakePatternHingeAxis.py", "MakePatternAnnotationCatalog.py", "PatternAngleArc.py")}}
    with args.output.open("xb") as stream:
        stream.write(encode(report))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
