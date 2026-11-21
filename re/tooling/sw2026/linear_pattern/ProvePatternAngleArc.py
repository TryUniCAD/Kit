from argparse import ArgumentParser
from math import cos, dist, hypot, radians, sin
from pathlib import Path
from struct import pack, unpack
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckPatternAngleOwners import check_angles, node_fields, point, require, roots_of_kind
from PatternAngleArc import ARC_TOLERANCE, INITIAL_TEXT_PARAMETER, OPEN_ARC_LIMIT_RAD, exterior_side, make_angle_arc_fields
from PatternAngleGeometry import WITNESS_RADIUS
from PatternAngleWire import ANGLE_PLANE, read_resolved, write_resolved
from PatternEnvelopeSpec import specification
from PatternHingeGeometry import ORIGIN
from ProvePatternAngleOwners import PROVEN_HINGE, exact_config
from ProvePatternPlaneDirectionRule import Image, MEASUREMENTS, MODULES, checked, digest, document_rows, double_at, encode, module
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeRawIdentity import MakeRawIdentity


SOURCE_OWNERS = "adf414b19f9e6c9e47463dad4ea4799fd3de589dca4099edeb625abb59240498"
ANNOTATION = "6d763f146c13b64014a73fe5c07c830664742b9bf5401a248352bf94740aab68"
MODULE_SPANS = {
    "base_display_initialization": (0x4C88A1E0, 0x4C88A673, "26b25fd6dda4d0294f77cfbdbcabd98e111861194e2f91e92fcc0cd59988f09d"),
    "feature_arc_constructor": (0x4C85AAE0, 0x4C85AB7A, "064c3b044baf9c668217ede271e4cf669d18673d23a844e6e42bfc9c095e8273"),
    "arc_seed_fields": (0x4C862790, 0x4C862810, "c9a13d2485d095d0da42e23f3a72b6b518ddacc59e775be7f5bc6d327f9787db"),
    "datum_adornment": (0x4B8F4FA0, 0x4B8F5986, "a6edd279997adff6f12087cbaf5d0d209ad830959159741ea3d49ff940d20813"),
    "new_label_update": (0x4C866BD0, 0x4C866DAF, "980082355c8b89b90687d6171c2ad5fb10d122c261e351964ad2b44104ea7851"),
    "existing_label_update": (0x4C866DB0, 0x4C867321, "f267442436390d631dfce2198cfe47361fc6d055ef7b2842b12fa802b65bbb49"),
    "witness_centre_and_radius": (0x4C861870, 0x4C86276D, "d813d8eecf25a1d6eb5d5548ffd932ce3f77456573bb6bbfb4399aa9d3d5ffd6"),
    "update_angle_def": (0x4C866450, 0x4C866A10, "595798f0942711ff80bf97be479ff5f92c2cdcf13115279f83efeb6d17f4919a"),
    "double_angle_guard": (0x4C863720, 0x4C863752, "459b2994c0cf6a003ee92cae613ac14e1b84ebe7832688ba4207fca42c17cd3b"),
    "choose_text_parameter": (0x4C860820, 0x4C860DD9, "d0cc817381a2e154cafa64999e255ae93ba7c63b5cf1965e5614f873f4a57ade"),
    "set_text_parameter": (0x4C8984A0, 0x4C8984A9, "e6fd45f7076d93f50965ff7384e445d49c8d48a05cd05ea1f82c5b9052cea9f4"),
    "set_text_radius": (0x4C8995E0, 0x4C8995E9, "893d80e75a8f4b28468562d7ba6b94b8f795c25cc8ee69229fe47977918419ca"),
    "serialize_angle_tail": (0x4C82B8F0, 0x4C82BE01, "85fdae2dd30cf8baf74d28fef9d6f7b36a4f7982c7dfaf8c93f7bc1ee74e204d"),
    "serialize_display_base": (0x4C82C3D0, 0x4C8310DA, "1590b966dad82241f29d36dd8d02182b006a423eedc91f7dd9014d1ef9986fd2"),
}
MATH_SPANS = {
    "line_intersection": (0x31E1DE80, 0x31E1DEAC, "004f91ca836efeca9c5e3a7c3e9de6be53707d3f2c56dfcbab3c482b1c69bb95"),
    "intersect_normalized_rays": (0x31E24B10, 0x31E24E00, "ee3bc86ee12edaf27673da794a849efbea4f02db6cb32aaa8e49de8aa8ecbaab"),
    "raw_transform_writer": (0x31F1D9A0, 0x31F1DA7D, "20ffb94cf1d4e4714e02f56bc25bea180527ffe137015b84b80a4224fd41a4c9"),
}


def span_report(image, spans):
    report = {}
    for role, (start, end, expected) in spans.items():
        require(digest(image.bytes(start, end)) == expected, "pinned angular display code changed for " + role)
        report[role] = {"range": [hex(start), hex(end)], "sha256": expected}
    return report


def static_owners(directory):
    model, math = (Image(directory / name) for name in MODULES)
    modules = [module(image, MODULES[image.path.name]) for image in (model, math)]
    constants = {
        "ordinary_text_midpoint": (0x4CD9A3C0, INITIAL_TEXT_PARAMETER),
        "outside_first_witness": (0x4CE32CB8, -INITIAL_TEXT_PARAMETER),
        "outside_second_witness": (0x4CDE9A88, 1.5),
        "native_comparison_tolerance": (0x4CD9A3B0, ARC_TOLERANCE),
        "ordinary_arc_mode_threshold": (0x4D1BD400, OPEN_ARC_LIMIT_RAD),
        "witness_m": (0x4CDDCD28, WITNESS_RADIUS),
    }
    slots = {"initial_position": (0x9C0, 0x4C866BD0), "existing_position": (0x9C8, 0x4C866DB0),
             "derive_geometry": (0xD10, 0x4C861870), "update_radius": (0x5E8, 0x4C8995E0)}
    for offset, expected in slots.values():
        address = 0x4D247828 + offset
        require(unpack("<Q", model.bytes(address, address + 8))[0] == expected, "native angular display slot changed")
    for address, expected in constants.values():
        require(double_at(model, address) == expected, "pinned angular display arithmetic constant changed")
    bindings = {
        "cross": (0x4CD3A978, "??D@YA?AVmgVector_c@@AEBV0@0@Z"),
        "dot": (0x4CD3A600, "??L@YANAEBVmgVector_c@@0@Z"),
        "intersect": (0x4CD3BDB8, "?mg_LineIntLine@@YA?AW4mgIntersectionType_e@@AEBVmgPoint_c@@AEBVmgVector_c@@01PEAV2@N@Z"),
        "write_raw_transform": (0x4CD3B538, "??6@YAAEAVsu_CArchive@@AEAV0@AEAVmgXform_c@@@Z"),
    }
    for address, symbol in bindings.values():
        entry = model.imports[address]
        require(entry["module"].casefold() == math.path.name and entry["symbol"] == symbol,
                "angular geometry no longer calls its pinned math owner")
    return {"modules": modules, "display_spans": span_report(model, MODULE_SPANS),
            "math_spans": span_report(math, MATH_SPANS),
            "angular_display_virtual_slots": {role: list(map(hex, item)) for role, item in slots.items()},
            "math_imports": {role: hex(address) for role, (address, _) in bindings.items()},
            "constants": {role: [hex(address), value] for role, (address, value) in constants.items()}}


def compare_fields(predicted, saved):
    equivalent, errors = [], {}
    for key, expected in predicted.items():
        actual = saved[key]
        if type(expected) is dict:
            actual, expected = point(actual), point(expected)
            errors[key] = dist(actual, expected)
            same_bits = pack("<3d", *actual) == pack("<3d", *expected)
        elif type(expected) is float:
            require(type(actual) is float, "wrong angular display scalar kind for " + key)
            errors[key] = abs(actual - expected)
            same_bits = pack("<d", actual) == pack("<d", expected)
        else:
            require(type(actual) is int and actual == expected, "wrong angular display selector for " + key)
            same_bits = True
        tolerance = 2e-15 if key in ("f880", "ffb8", "ffd0") else 1e-16
        require(errors.get(key, 0.0) <= tolerance and (key != "f8a8" or same_bits),
                "arc field differs from independent geometry or native text branch for " + key)
        if same_bits:
            equivalent.append(key)
    return {"binary_equal_fields": equivalent, "absolute_errors": errors}


def altered_states(predicted, display):
    changes = (
        ("unupdated_constructor_midpoint", {"f8a8": INITIAL_TEXT_PARAMETER}),
        ("unupdated_constructor_radius", {"f8b0": 0.0}),
        ("swapped_first_second_witness", {"f958": display["f988"], "f988": display["f958"]}),
        ("opposite_first_ray", {"ffb8": {"x": 0.0, "y": -1.0, "z": 0.0}}),
        ("wrong_constructor_mask", {"f1018": display["f1018"] | 4}),
    )
    refused = {}
    for label, mutant in changes:
        try:
            compare_fields(predicted, {**display, **mutant})
        except ValueError as error:
            refused[label] = str(error)
    require(len(refused) == len(changes), "an altered arc placement or role escaped strict comparison")
    return refused


def display_context(display):
    actual = tuple(word["w"] for word in display["f5c0"]["words"])
    identity = tuple(word["w"] for word in MakeRawIdentity()["words"])
    differences = [index for index, words in enumerate(zip(actual, identity, strict=True)) if words[0] != words[1]]
    require(differences == [19], "angular display transform differs from ordinary identity outside its ignored padding")
    return {"observed_leader": display["ff80"], "identity_padding": {"word_index": 19, "source": actual[19], "canonical": identity[19]}}


def disclosed(share):
    hinge = json.loads(checked(MEASUREMENTS / "LocalLinearPatternFiniteHinge01.json", PROVEN_HINGE))
    previous = json.loads(checked(MEASUREMENTS / "LocalLinearPatternAngularDatumOwners01.json", SOURCE_OWNERS))["disclosed_cases"]
    checked(MEASUREMENTS / "LocalLinearPatternAnnotationCatalog01.json", ANNOTATION)
    ends = {name: tuple(map(tuple, case["from_authored_boxes"]["ordered_endpoints_m"]))
            for case in hinge["disclosed_cases"].values() for name in case["typed_saves"]}
    angle = specification()["direction_datum"]["arguments"][1]
    cases = {}
    for path, pin, row in document_rows(share):
        if row["plane_data_class"] != ANGLE_PLANE:
            continue
        require(previous[path.name]["sha256"] == pin, "the actual disclosed angular specimen changed")
        archive, headers, config, config_bytes = exact_config(path, pin)
        link = MakeLinkContext(config, ReadCmgrMut(archive.require("Contents/CMgr"), 19000))
        raw = archive.require("Contents/Config-0-ResolvedFeatures")
        roots, extra, read_map = read_resolved(raw, config.MapValue, link, source_replay=True)
        replay, written = write_resolved(roots, extra, config.MapValue, link, source_replay=True)
        counters = [config.MapValue.CounterValue, read_map.CounterValue]
        require(replay == raw and read_map == written and extra is not None and len(roots) == previous[path.name]["root_count"]
                and counters == previous[path.name]["map_counters"], "stored angular graph changed replay bytes or linked owners")
        joined = check_angles(config.RootValue, roots, headers, ends[path.name], angle)
        (feature,) = [node for node in roots_of_kind(roots, "moRefPlane_c") if node.FieldsValue["f08"] == joined["feature"]["id"]]
        display = node_fields(node_fields(feature.FieldsValue["f6f8"], ANGLE_PLANE)["f150"], "moDisplayAngularDim_c")
        require(display["fb64"] & 0x03008002 == 0 and display["f1018"] & 7 == 0,
                "saved witnesses require another arc geometry or reference-order branch")
        predicted = make_angle_arc_fields(*ends[path.name], angle)
        side = exterior_side(point(display["ffb8"]), point(display["ffd0"]), point(display["f880"]))
        require(side < -ARC_TOLERANCE, "actual saved label lies outside the proved first-witness branch")
        cases[path.name] = {"sha256": pin, "config_sha256": digest(config_bytes), "resolved_sha256": digest(raw),
                            "linked_stream_sizes": [len(config_bytes), len(raw)], "root_count": len(roots),
                            "map_counters": counters, "actual_driver": joined["driver"], "first_witness_side": side,
                            "actual_fields": {field: display[field] for field in predicted},
                            "comparison": compare_fields(predicted, display), "refusals": altered_states(predicted, display),
                            "display_context_outside_arc": display_context(display)}
    require(len(cases) == 4 and len({row["display_context_outside_arc"]["observed_leader"] for row in cases.values()}) == 2,
            "the four disclosed angular graphs or independent display style contrast changed")
    return cases


def model_case(label, width, depth, degrees):
    angle = radians(degrees)
    request = {"plate_box_m": ((0.0, 0.0, 0.0), (width, 0.08875, 0.00475)),
               "raised_box_m": ((0.03125, 0.0185, 0.0), (0.0425, 0.03625, depth)),
               "angle_rad": angle, "reverse": False}
    input_data = encode(request)
    argv = (sys.executable, "-I", "-B", str(HERE.with_name("PatternAngleArcProcess.py")))
    first, second = (run(argv, cwd=ROOT, input=input_data, capture_output=True, check=True, timeout=20) for _ in range(2))
    require(not first.stderr and not second.stderr and first.stdout == second.stdout, "generated angular arc is not deterministic")
    result = json.loads(first.stdout)
    fields = result["fields"]
    local_second_witness = (-WITNESS_RADIUS * sin(angle), WITNESS_RADIUS * cos(angle), 0.0)
    offset_x = depth * 0.55 * sin(angle) - WITNESS_RADIUS * sin(angle * 0.5)
    offset_y = WITNESS_RADIUS * cos(angle * 0.5) - depth * 0.55 * cos(angle)
    independent_radius = hypot(offset_x, offset_y)
    expected_direction = (offset_x / independent_radius, offset_y / independent_radius, 0.0)
    require(result["guarded_runtime_reads"] == result["cad_files_written"] == 0 and len(result["refusals"]) == 5
            and result["field_slice_bytes"] == 257 and offset_x > 0.0 and fields["f8a8"] == -0.5
            and dist(point(fields["f988"]), local_second_witness) < 1e-16 and dist(point(fields["f9b8"]), ORIGIN) < 1e-16
            and dist(point(fields["f880"]), expected_direction) < 2e-15 and abs(fields["f8b0"] - independent_radius) < 1e-16,
            "generated angular arc disagrees with the independent closed-form placement")
    return {"neutral_intent_sha256": digest(input_data), "label": label, "angle_degrees": degrees,
            "closed_form_radius_m": independent_radius, "closed_form_second_witness_m": local_second_witness, **result}


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    models = [model_case("ExteriorAlpha", 0.12725, 0.017375, 28.625), model_case("ExteriorBeta", 0.148125, 0.026125, 63.125)]
    require(models[0]["field_slice_sha256"] != models[1]["field_slice_sha256"], "independent authored arc fields became invariant")
    reports = {"schema": "kit.sw2026.research-only.constrained-angle-arc.v1", "static_owners": static_owners(args.binaries),
               "disclosed_graphs": disclosed(args.disclosed_share), "neutral_model_proofs": models,
               "earlier_evidence_sha256": [PROVEN_HINGE, SOURCE_OWNERS, ANNOTATION], "guarded_model_processes": 4,
               "cad_files_written": 0, "native_calls": 0, "heldout_accesses": 0,
               "full_display_owner_represented": False, "full_angular_feature_represented": False,
               "tools": {name: digest(HERE.with_name(name).read_bytes()) for name in
                         ("PatternAngleArc.py", "PatternAngleArcProcess.py", "PatternAngleGeometry.py",
                          "PatternPlaneDirectionRule.py", "PatternAngleWire.py", "CheckPatternAngleOwners.py", HERE.name)}}
    with args.output.open("xb") as file:
        file.write(encode(reports))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
