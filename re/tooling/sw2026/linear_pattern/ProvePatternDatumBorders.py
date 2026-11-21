from argparse import ArgumentParser
from math import isfinite, pi
from pathlib import Path
from struct import pack, unpack
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from AuditPatternDatumPlacement import ANGLE_PLANE, DEFAULT_PLANE, ZERO, geometry_fields, replay
from AuditPatternEnvelope import Obj, need_node, node_name, vector
from ProvePatternPlaneDirectionRule import HEIGHTS, RECTANGLES, double_at, document_rows
from ProvePatternPlaneDirectionRule import Image, MODULES, checked, digest, encode, module, require, resolve_local_plane


ANGLE_VTABLE = 0x4CED1C20
LINE_VTABLE = 0x4CE5CD20
SLOTS = {
    "geometry_extents": (ANGLE_VTABLE, 0x178, 0x4B8EB7B0),
    "build_borders": (ANGLE_VTABLE, 0x180, 0x4B8E3430),
    "point_alternative": (ANGLE_VTABLE, 0x190, 0x4B8E7B70),
    "check_borders": (ANGLE_VTABLE, 0x198, 0x4C2EB520),
    "expand_borders": (ANGLE_VTABLE, 0x1A0, 0x4B27E150),
    "adjust_normal": (ANGLE_VTABLE, 0x1D0, 0x4B8EAF20),
    "update_dimension_adornment": (ANGLE_VTABLE, 0x240, 0x4B8EF0C0),
    "is_straight_line": (LINE_VTABLE, 0xE0, 0x4B27E150),
    "get_line_endpoints": (LINE_VTABLE, 0x3F8, 0x4C316200),
}
RANGES = {
    "build_borders": (0x4B8E3430, 0x4B8E3655, "233143482f3b38480619e97f03ff1d96e91bbbb24eb08b00e962f1d6d1422a56"),
    "geometry_extents": (0x4B8EB7B0, 0x4B8EBD96, "28389034cf9e9b9440d245d49ad9748bb9e747bd8b26992b6349fb61d04d1f90"),
    "straight_line_extents": (0x4B8EB94A, 0x4B8EBAA6, "af72c60efcab460c4ade2608ed9f89676d0e71419a9e75f2218de4f464646b5a"),
    "reference_axis_endpoints": (0x4C316875, 0x4C316975, "e2586339856ca9ae197b497417cdd079a4314815bcafc1e876c7e95840565dba"),
    "axis_updated_points": (0x4C27E830, 0x4C27E894, "31d395f247314119cd141f8926ecabc38d9610a75fe25aee1c58a6812a737bce"),
    "extract_borders": (0x4C2E3690, 0x4C2E3727, "6db1b7a3be08d2b08c299129893e8c44230c8d69e0c6ad3a86ae0267edae531f"),
    "check_borders": (0x4C2EB520, 0x4C2EB65F, "118bed4a7be955a6a4f4822eae314e83189853d3fdb329116520e8347de5a74c"),
    "expand_borders": (0x4C2DBDD0, 0x4C2DBE59, "bd92371068e679a628975661da7e5037d7b60555a3fcfbcb8126b660e3be78d7"),
    "true_leaf": (0x4B27E150, 0x4B27E156, "2db31f4e09597946e56e859813bfdad7046d457c32332c3a882654d1e3ffdf67"),
}
IMPORTS = {
    "include_endpoint": (0x4CD3AA80, "??_5mgBBox_c@@QEAAAEAV0@AEBVmgPoint_c@@@Z"),
    "transform_extents": (0x4CD3AA78, "??XmgBBox_c@@QEAAAEAV0@AEBVmgXform_c@@@Z"),
}
CONSTANTS = {"minimum_span_m": (0x4CDD64F0, 1e-7), "edge_fraction": (0x4CDDCA68, 0.05)}
U = (0.0, 0.0, -1.0)


def read_bindings(path):
    image = Image(path)
    identity = module(image, MODULES["sldmodu.dll"])
    slots = {}
    for role, (vtable, offset, target) in SLOTS.items():
        address = vtable + offset
        require(unpack("<Q", image.bytes(address, address + 8))[0] == target, "changed vtable binding " + role)
        slots[role] = {"vtable_va": hex(vtable), "slot": hex(offset), "target_va": hex(target)}
    ranges = {}
    for role, (start, end, expected) in RANGES.items():
        require(digest(image.bytes(start, end)) == expected, "changed code range " + role)
        ranges[role] = {"start_va": hex(start), "end_va_exclusive": hex(end), "sha256": expected}
    imports = {}
    for role, (address, symbol) in IMPORTS.items():
        actual = image.imports[address]
        require(actual == {"module": "sldmgu.dll", "symbol": symbol}, "changed import binding " + role)
        imports[role] = {"iat_va": hex(address), **actual}
    constants = {}
    for role, (address, expected) in CONSTANTS.items():
        require(double_at(image, address) == expected, "changed geometry constant " + role)
        constants[role] = {"va": hex(address), "binary64": expected}
    return {"module": identity, "slots": slots, "ranges": ranges, "imports": imports, "constants": constants}


def key_of(reference, wrapper_class, selected_class, model):
    wrapper = need_node(reference, wrapper_class)
    selected = need_node(wrapper["f58"], selected_class)
    component = need_node(selected["f58"], "moUnitComponent_c")
    require(wrapper["f60"] is None and component["owner"] is model and component is not model["f990"],
            "expected an untransformed reference to the same local part")
    return selected["ff0"]["f00"]


def root_with_key(roots, class_name, key):
    matches = [node for node in roots if isinstance(node, Obj) and node.cls == class_name and node["f08"] == key]
    require(len(matches) == 1, "reference key does not resolve to one typed root")
    return matches[0]


def padded_borders(start, finish, horizontal):
    minimum_span = CONSTANTS["minimum_span_m"][1]
    edge_fraction = CONSTANTS["edge_fraction"][1]
    require(horizontal == U and start[:2] == finish[:2] == ZERO[:2]
            and all(isfinite(point[2]) for point in (start, finish)) and start[2] > 0.0 > finish[2],
            "expected a through-origin finite signed vertical hinge")
    high, low = -finish[2], -start[2]
    span = abs(high - low)
    require(isfinite(span) and span > minimum_span, "native zero-span fallback is outside the reconstruction")
    padding = span * edge_fraction
    return high + padding, low - padding, span + padding, 0.0 - padding


def prove_case(path, pin, prior):
    model, roots, replay_stats = replay(checked(path, pin))
    placement = geometry_fields(model, roots, ANGLE_PLANE)
    require(encode(placement) == encode(prior), "previous native placement reading differs")
    plane = root_with_key(roots, "moRefPlane_c", placement["plane_id"])
    data = need_node(plane["f6f8"], ANGLE_PLANE)
    constraints = need_node(data["f88"], "moConstraintRefplaneInterfaceData_c")
    angle = need_node(constraints["f08"], "moRefPlaneAngleGeom_c")
    coincident = need_node(constraints["f10"], "moRefPlaneCoincidentGeom_c")
    alternate = need_node(constraints["f18"], "moRefPlaneCoincidentGeom_c")
    hinge_ref = need_node(coincident["f08"], "moLineRef_w")
    right = key_of(angle["f08"], "moPlaneRef_w", "moCompRefPlane_c", model)
    hinge_id = key_of(hinge_ref, "moLineRef_w", "moCompRefAxis_c", model)
    require(angle["f38"] == pi / 4.0 and angle["f40"] == 0 and alternate["f08"] is None,
            "selected angle or constraint roles are outside the measured profile")
    axis = root_with_key(roots, "moRefAxis_c", hinge_id)
    axis_data = need_node(axis["f700"], "moPlaneInterAxisData_c")
    top = key_of(axis_data["f80"], "moPlaneRef_w", "moCompRefPlane_c", model)
    require(top != right and key_of(axis_data["f88"], "moPlaneRef_w", "moCompRefPlane_c", model) == right,
            "independent hinge plane references are crossed")
    for key, expected_normal in ((top, (0.0, 1.0, 0.0)), (right, (1.0, 0.0, 0.0))):
        base_data = need_node(root_with_key(roots, "moRefPlane_c", key)["f6f8"], DEFAULT_PLANE)
        require(vector(base_data["root"]) == ZERO and vector(base_data["normal"]) == expected_normal,
                "hinge reference lost its canonical through-origin geometry")
    start, finish = vector(axis_data["f18"]), vector(axis_data["f30"])
    horizontal, _, normal = placement["basis_u_v_n"]
    require(vector(axis_data["f68"]) == ZERO and vector(axis_data["f50"]) == horizontal == U
            and axis_data["f08"] == start[2] and axis_data["f10"] == -finish[2]
            and vector(hinge_ref["fc8"]) == start and vector(hinge_ref["fe0"]) == U
            and hinge_ref["fb0"] == 0.0 and hinge_ref["fb8"] == start[2] - finish[2] and hinge_ref["f68"] == 1,
            "axis endpoints and signed line wrapper do not agree")
    borders = padded_borders(start, finish, horizontal)
    require(pack("<4d", *borders) == pack("<4d", *placement["ordered_borders_m"]), "derived borders differ from saved words")
    (pattern,) = [node for node in roots if isinstance(node, Obj) and node.cls == "moLPattern_c"]
    pattern_ref = need_node(pattern["f1288"], "moLineRef_w")
    require(key_of(pattern_ref, "moLineRef_w", "moCompRefPlane_c", model) == plane["f08"], "pattern references a different datum")
    direction = resolve_local_plane(ZERO, horizontal, normal, borders)
    require(pack("<8dB", *direction["fc8"], *direction["fe0"], direction["fb0"], direction["fb8"], direction["f68"])
            == pack("<8dB", *vector(pattern_ref["fc8"]), *vector(pattern_ref["fe0"]),
                    pattern_ref["fb0"], pattern_ref["fb8"], pattern_ref["f68"]), "derived direction differs from saved words")
    return {"native_file": path.name, "sha256": pin, "datum": {"id": plane["f08"], "name": node_name(plane),
            "archive_object": plane.index, "data_class": data.cls},
            "hinge": {"id": hinge_id, "name": node_name(axis), "archive_object": axis.index,
                      "line_object": hinge_ref.index, "signed_endpoint_order_m": [start, finish], "top_right_ids": [top, right]},
            "borders_m": borders, "direction": direction, "exact_binary64": True, **replay_stats}


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bindings = read_bindings(args.binaries / "sldmodu.dll")
    rows = [prove_case(path, pin, row) for path, pin, row in document_rows(args.disclosed_share)
            if row["plane_data_class"] == ANGLE_PLANE]
    require(len(rows) == 4 and len({row["sha256"] for row in rows}) == 4
            and len({row["borders_m"] for row in rows}) == 3, "disclosed angle-plane contrast differs")
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "host proof imported CAD dependencies")
    result = {"schema": "kit.sw2026.linear-pattern-datum-borders.v1", "static_native_bindings": bindings,
              "source_receipt_sha256": [RECTANGLES, HEIGHTS], "disclosed_cases": rows,
              "proof_sha256": digest(HERE.read_bytes()), "exact_border_binary64_words": 4 * len(rows),
              "exact_direction_fields": 5 * len(rows), "exact_linked_stream_replays": 2 * len(rows),
              "native_processes_started": 0, "held_out_inputs_read": 0, "cad_files_written": 0}
    with args.output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"receipt_sha256": digest(args.output.read_bytes()), "disclosed_cases": len(rows),
                      "exact_border_binary64_words": result["exact_border_binary64_words"]}))


if __name__ == "__main__":
    main()
