from argparse import ArgumentParser
from pathlib import Path
from struct import pack, unpack
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from AuditPatternDatumHeight import source_records
from AuditPatternDatumPlacement import ANGLE_PLANE, DEFAULT_PLANE, geometry_fields, replay
from AuditPatternEnvelope import ARTIFACTS, Obj, lifecycle, need_node, node_name, vector
from PatternDatumHeightPacket import CASE_NAMES, TRIAL, arm_spec, verified_plan, verify
from PatternHingeGeometry import AXIS, EDGE_FRACTION, MINIMUM_SPAN_M, ORIGIN, derive_hinge, principal_displays
from ProvePatternDatumBorders import key_of, padded_borders, root_with_key
from ProvePatternPlaneDirectionRule import HEIGHTS, MEASUREMENTS, MODULES, RECTANGLES, Image
from ProvePatternPlaneDirectionRule import checked, digest, double_at, encode, module, require, resolve_local_plane


MODEL_SLOTS = {
    "default_plane_bounds": (0x4D138FF0, 0x178, 0x4C2ECB70),
    "default_plane_projected_spans": (0x4D138FF0, 0x170, 0x4C2F0C90),
    "default_plane_set_borders": (0x4D138FF0, 0x188, 0x4C2F65A0),
    "part_model_bounds": (0x4D1252D8, 0x1350, 0x4B57A7E0),
    "intersect_both_planes": (0x4D162258, 0x90, 0x4C286CA0),
    "clip_to_first_plane": (0x4D162258, 0xE8, 0x4C289060),
    "plane_reference_corners": (0x4CF52068, 0x240, 0x4C31E9A0),
}
MODEL_RANGES = {
    "default_plane_ctor": (0x4C2D9BA0, 0x4C2D9C74, "b0260e3a3fe4a1d703f35ce0db0411afbc4eb267be24f6969c0ad7ab2658c3aa"),
    "default_plane_set_borders": (0x4C2F65A0, 0x4C2F67B9, "4f81bccfdc8dea0b78f7e09488333b513ca1f7cfe620e9bef3406f34f8a6daad"),
    "default_plane_projected_spans": (0x4C2F0C90, 0x4C2F0DFC, "02a2f598389bdd5888a52e9cb93ce2ec6ae520b3a31a211f5d321325a6e2e21e"),
    "default_plane_bounds": (0x4C2ECB70, 0x4C2ECCB9, "0bfb1c3a11ed6ad60ba61d2d194fd0f73ce748e60d565100e937fea6c89bc99f"),
    "part_box_entry": (0x4B57A7E0, 0x4B57A82C, "57feee002329c4318e0234d825404676bb7014bfd18f33b447e7c2fc07e7d7de"),
    "part_box_provider": (0x4B581040, 0x4B581568, "cef97fd71339e25173d80c3460c3a0319dc2972d673bf1c6d496e0dea1df88a7"),
    "intersect_both_planes": (0x4C286CA0, 0x4C286E6D, "4b52191005be97a10d23f2e71956252f0556f30b0e916ecd7a30359a93b1b726"),
    "clip_to_first_plane": (0x4C289060, 0x4C28954D, "37b77650c73184eebd1883d7363a43076547d1e65dc4ad68173df91e14efd0ba"),
    "store_signed_sizes": (0x4C2886C0, 0x4C28890F, "38bd8984cdf9d1bf5df01ab392bc87897fe7c72be0b899e41c760e7ea90d3180"),
    "get_finite_axis_endpoints": (0x4C288230, 0x4C28851A, "ae5bd6e2f8bbb2589d1a89d3d8259c29aa2cd98224fd483cadcfef8f58823093"),
    "plane_intersection_axis_data_ctor": (0x4C281520, 0x4C281683, "612c77b8a8ec861aaa7c327dfa62d1af2c1971af75149e95823934b0d6b618ef"),
    "selected_plane_corners": (0x4C31FBC0, 0x4C31FEA0, "b56e17ce3f00c416127f42a322a93449585df173a669b5d4a5d8c22255cc0578"),
}
MATH_CENTER = (0x31DE1100, 0x31DE11B8, "04b7a4ddceb2579748ca356e23605fb259aa7b3d9510e9030c4631d8a73595e6")
MODEL_CONSTANTS = {
    "half_span": (0x4CD9A3C0, 0.5), "negative_half_span": (0x4CE32CB8, -0.5),
    "edge_fraction": (0x4CDDCA68, EDGE_FRACTION), "minimum_span_m": (0x4CDD64F0, MINIMUM_SPAN_M),
}
PRESENTATION_NORMALS = {"Top Plane": (0.0, 1.0, 0.0), "Right Plane": (1.0, 0.0, 0.0)}


def code_span(image, span):
    start, end, sha256 = span
    require(digest(image.bytes(start, end)) == sha256, "changed static rule range " + hex(start))
    return {"start_va": hex(start), "end_va_exclusive": hex(end), "sha256": sha256}


def static_bindings(directory):
    model, math = (Image(directory / name) for name in MODULES)
    modules = [module(image, MODULES[image.path.name]) for image in (model, math)]
    slots = {}
    for role, (vtable, offset, target) in MODEL_SLOTS.items():
        address = vtable + offset
        require(unpack("<Q", model.bytes(address, address + 8))[0] == target, "changed concrete slot " + role)
        slots[role] = (hex(vtable), hex(offset), hex(target))
    constants = {}
    for role, (address, expected) in MODEL_CONSTANTS.items():
        require(double_at(model, address) == expected, "changed source constant " + role)
        constants[role] = {"va": hex(address), "binary64": expected}
    center_import = model.imports[0x4CD3A6C0]
    require(center_import == {"module": "sldmgu.dll", "symbol": "?center@mgBBox_c@@QEBA?AVmgPoint_c@@XZ"}
            and center_import["symbol"] in math.exports[MATH_CENTER[0]]
            and double_at(math, 0x31F44820) == 0.5, "changed bounded model center arithmetic")
    return {"modules": modules, "concrete_slots": slots, "model_constants": constants,
            "model_ranges": {role: code_span(model, span) for role, span in MODEL_RANGES.items()},
            "center_import": center_import, "center_provider": code_span(math, MATH_CENTER)}


def observations(record, expected, phase):
    calls = record["api_calls"]
    axes = [index for index, row in enumerate(calls) if row["method"] == "GetRefAxisParams"]
    count = {"author": 3, "spacing-edit": 2}.get(phase, 1)
    require(len(axes) == count, "axis getter count differs " + phase)
    if phase == "author":
        (insert_axis,) = [index for index, row in enumerate(calls) if row["method"] == "InsertAxis2"]
        (insert_plane,) = [index for index, row in enumerate(calls) if row["method"] == "InsertRefPlane"]
        (insert_pattern,) = [index for index, row in enumerate(calls) if row["method"] == "CreateFeature"]
        require(calls[insert_axis]["result"] is True
                and insert_axis < axes[0] < insert_plane < axes[1] < insert_pattern < axes[2],
                "axis is not observed immediately after its creation and before its downstream geometry")
        stages = ("before_angle_plane", "before_pattern", "after_pattern")
    elif phase == "spacing-edit":
        stages = ("before_spacing_edit", "after_spacing_edit")
    else:
        stages = ("fresh_reopen",)
    words = pack("<6d", *expected[0], *expected[1])
    for index in axes:
        value = calls[index]["result"]
        require(type(value) is list and len(value) == 6 and pack("<6d", *value) == words,
                "analytic finite endpoints differ from the native getter at " + phase)
    return [{"stage": stage, "api_call_index": index} for stage, index in zip(stages, axes, strict=True)]


def check_display(node, expected):
    name = node_name(node)
    data = need_node(node["f6f8"], DEFAULT_PLANE)
    basis = data["f20"]["f08"]
    direction = tuple(tuple(basis[f"m{3 * axis + k}"] for axis in range(3)) for k in range(3))
    standard = {"Top Plane": ((1.0, 0.0, 0.0), AXIS), "Right Plane": (AXIS, (0.0, 1.0, 0.0))}
    normal = PRESENTATION_NORMALS[name]
    require(direction == (*standard[name], normal) and vector(data["root"]) == ORIGIN and vector(data["normal"]) == normal,
            "principal plane has a different measured basis")
    actual = (*vector(data["display_root"]), *(data[f"b{i}"] for i in range(4)))
    require(pack("<7d", *actual) == pack("<7d", *expected["display_root_m"], *expected["borders_m"]),
            "model-derived principal display differs from saved words for " + name)
    return {"id": node["f08"], "archive_object": node.index, **expected}


def prove_saved(raw, shape, predicted, arm):
    model, roots, linked = replay(raw)
    placement = geometry_fields(model, roots, ANGLE_PLANE)
    datum = root_with_key(roots, "moRefPlane_c", placement["plane_id"])
    constraints = datum["f6f8"]["f88"]
    hinge = key_of(constraints["f10"]["f08"], "moLineRef_w", "moCompRefAxis_c", model)
    axis_data = need_node(root_with_key(roots, "moRefAxis_c", hinge)["f700"], "moPlaneInterAxisData_c")
    start, finish = predicted["ordered_endpoints_m"]
    require(pack("<8d", *start, *finish, *predicted["ordered_distances_m"])
            == pack("<8d", *vector(axis_data["f18"]), *vector(axis_data["f30"]), axis_data["f08"], axis_data["f10"])
            and vector(axis_data["f50"]) == AXIS and vector(axis_data["f68"]) == ORIGIN,
            "model-derived signed hinge differs from its saved plane-intersection data")
    bounds = shape["arms"][arm]["expected_final"]["bounds_m"]
    bound_displays = principal_displays((bounds[:3], bounds[3:]))
    selected = {}
    for field, name in (("f80", "Top Plane"), ("f88", "Right Plane")):
        key = key_of(axis_data[field], "moPlaneRef_w", "moCompRefPlane_c", model)
        principal = root_with_key(roots, "moRefPlane_c", key)
        require(node_name(principal) == name, "resolved dimension is owned by a different principal plane")
        selected[name] = check_display(principal, bound_displays[name])
    horizontal, _, normal = placement["basis_u_v_n"]
    borders = padded_borders(start, finish, horizontal)
    require(pack("<4d", *borders) == pack("<4d", *placement["ordered_borders_m"]), "derived angled border comparison failed")
    direction = resolve_local_plane(ORIGIN, horizontal, normal, borders)
    require(pack("<3d", *direction["fc8"]) == pack("<3d", *placement["fc8_point_m"]),
            "derived pattern point differs across the hinge-to-datum chain")
    return {"sha256": digest(raw), "signed_hinge_id": hinge, "selected_principal_displays": selected,
            "angle_borders_m": borders, "pattern_line_point_m": direction["fc8"], **linked}


def author_shape(shape, author):
    predicted = derive_hinge(shape["plate_box_m"], shape["seed_box_m"])
    low, high = predicted["before_pattern_box_m"]
    require(list((*low, *high)) == shape["expected_before_pattern"]["bounds_m"]
            and list((*low, *high)) == author["pre_pattern"]["bounds"]["minmax"],
            "typed cohort does not use the independently authored joined box before the pattern")
    return predicted


def disclosed(share):
    placement = json.loads(checked(MEASUREMENTS / "LocalLinearPatternDatumPlacement01.json", RECTANGLES))
    height = json.loads(checked(MEASUREMENTS / "LocalLinearPatternDatumHeightNative01.json", HEIGHTS))
    _, shape, records, payloads = lifecycle(share / "LinearPatternEnvelope02", placement["packet_sha256"],
                                            placement["native_result_sha256"])
    original = author_shape(shape, records["author"])
    ends = original["ordered_endpoints_m"]
    common = {phase: observations(record, ends, phase) for phase, record in records.items()}
    saves = {name: prove_saved(payloads[name], shape, original, arm) for arm, name in enumerate(ARTIFACTS)}
    require(saves[ARTIFACTS[0]]["selected_principal_displays"]["Top Plane"] !=
            saves[ARTIFACTS[1]]["selected_principal_displays"]["Top Plane"]
            and saves[ARTIFACTS[0]]["pattern_line_point_m"] == saves[ARTIFACTS[1]]["pattern_line_point_m"],
            "spacing contrast must move the saved Top display along X without moving the hinge or angled point")
    result = {"Envelope": {"from_authored_boxes": original, "native_axis_observations": common, "typed_saves": saves}}
    trial = share / TRIAL
    packet = trial / "Packet"
    manifest = verify(packet, height["packet_sha256"])
    plan = verified_plan(packet / "Spec.json")
    out = trial / "DisclosedHeights"
    summary = json.loads(checked(out / "Result.json", height["native_result_sha256"]))
    height_records = source_records(out, summary, manifest)
    for name in CASE_NAMES:
        authored = arm_spec(plan, name)
        phases = {phase: row for (label, phase), row in height_records.items() if label == name}
        predicted = author_shape(authored, phases["author"])
        saved = height["cases"][name]["artifact"]
        checkpoints = {phase: observations(record, predicted["ordered_endpoints_m"], phase) for phase, record in phases.items()}
        exact = prove_saved(checked(out / name / saved["name"], saved["sha256"], saved["bytes"]), authored, predicted, 0)
        result[name] = {"from_authored_boxes": predicted, "native_axis_observations": checkpoints, "typed_saves": {saved["name"]: exact}}
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bindings = static_bindings(args.binaries)
    cases = disclosed(args.disclosed_share)
    count = sum(len(stages) for case in cases.values() for stages in case["native_axis_observations"].values())
    saves = sum(len(case["typed_saves"]) for case in cases.values())
    require(count == 15 and saves == 4, "unexpected native or saved sample count")
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "host proof imported a CAD runtime")
    result = {"schema": "kit.sw2026.linear-pattern-finite-hinge.v1", "static_native_bindings": bindings,
              "source_receipt_sha256": [RECTANGLES, HEIGHTS], "disclosed_cases": cases,
              "first_native_axis_phase": "after_insert_axis_before_insert_angle_plane", "exact_live_axis_observations": count,
              "exact_endpoint_saves": saves, "exact_principal_borders_and_origins": 2 * saves, "linked_stream_replays": 2 * saves,
              "proof_sha256": digest(HERE.read_bytes()), "arithmetic_sha256": digest(HERE.with_name("PatternHingeGeometry.py").read_bytes()),
              "native_processes_started": 0, "held_out_inputs_read": 0, "cad_files_written": 0}
    with args.output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"receipt_sha256": digest(args.output.read_bytes()), "live_checks": count, "saved_archives": saves}))


if __name__ == "__main__":
    main()
