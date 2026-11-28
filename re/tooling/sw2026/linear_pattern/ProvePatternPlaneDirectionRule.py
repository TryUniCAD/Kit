from argparse import ArgumentParser
from pathlib import Path
from struct import pack, unpack
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1])]

from AuditPatternDatumPlacement import replay
from AuditPatternEnvelope import Obj, need_node, vector
from CollectDrawingViewSupportEvidence import Image, module
from PatternEnvelopePacket import checked, digest, encode, require
from PatternPlaneDirectionRule import resolve_local_plane


MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
RECTANGLES = "827baa41493ed7fc459dcb5d7b4485a733494cf20fd4fb8d9ecb5aee4a70f566"
HEIGHTS = "a82c6e544fec26fbb4c87f19da31f716df68d77f5169f27f0dddec25508b45d6"
MODULES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldmgu.dll": "99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c",
}
MODEL = {
    "get_plane_center": 0x4C2E4600,
    "get_plane_corners": 0x4C2E57C0,
    "compose_ordered_corners": 0x4C2ECDB0,
    "get_selected_plane": 0x4B285240,
    "get_selected_normal": 0x4C2D5440,
    "relative_transform": 0x4C30AE30,
}
IMPORTS = {
    "root_of_plane": 0x4CD3A920, "normal_of_plane": 0x4CD3A928,
    "point_plus_vector": 0x4CD3A5B0, "subtract_points": 0x4CD3A5C0,
    "scale_basis_vector": 0x4CD3A5F0, "add_basis_vectors": 0x4CD3ABA0,
    "cross_basis_vectors": 0x4CD3A978, "normalize_vector": 0x4CD3AAA0,
    "point_to_vector": 0x4CD3A8E0, "zero_vector_constructor": 0x4CD3AB28,
    "accumulate_corner": 0x4CD3A9E0, "divide_vector": 0x4CD3A8E8,
    "project_span_dot": 0x4CD3A600,
}
SPAN = (0x4C316200, 0x4C317C3F)


def double_at(image, address):
    return unpack("<d", image.bytes(address, address + 8))[0]


def read_bindings(directory):
    model, math = (Image(directory / name) for name in MODULES)
    indices = {export: address for address, names in math.exports.items() for export in names}
    model_probes = {role: model.function(address) for role, address in MODEL.items()}
    math_probes = {}
    for role, address in IMPORTS.items():
        imported = model.imports[address]
        require(imported["module"].casefold() == "sldmgu.dll", "unexpected math import owner")
        math_probes[role] = {"iat_address": hex(address), **imported, **math.function(indices[imported["symbol"]])}
    math_probes["unit_vector_constructor"] = math.function(indices["??0mgUnitVector_c@@QEAA@NNN@Z"])
    endpoint = (0x4CE5CD20 + 0x3F8, 0x4C316200)
    require(unpack("<Q", model.bytes(endpoint[0], endpoint[0] + 8))[0] == endpoint[1],
            "actual line-reference endpoint slot differs")
    expected = "e1a368e4dcb52b7e54df2edaefd4f3ace865a51becec4d244b47c34c219e8f10"
    require(digest(model.bytes(*SPAN)) == expected, "complete endpoint resolver no longer matches its native boundary")
    constants = {"corner_count_divisor": double_at(model, 0x4CDFDC60),
                 "unit_squared_threshold": double_at(math, 0x31F57960),
                 "vector_division_numerator": double_at(math, 0x31F44828)}
    require(constants == {"corner_count_divisor": 4.0, "unit_squared_threshold": 1e-17,
                          "vector_division_numerator": 1.0}, "geometry arithmetic constants differ")
    return {"modules": [module(src, MODULES[src.path.name]) for src in (model, math)],
            "model_probes": model_probes, "math_probes": math_probes, "constants": constants,
            "endpoint_vtable_slot": {"address": hex(endpoint[0]), "target": hex(endpoint[1]),
                                     "resolver_range": [hex(x) for x in SPAN], "resolver_sha256": expected}}


def document_rows(share):
    main = json.loads(checked(MEASUREMENTS / "LocalLinearPatternDatumPlacement01.json", RECTANGLES))
    heights = json.loads(checked(MEASUREMENTS / "LocalLinearPatternDatumHeightNative01.json", HEIGHTS))
    principal = share / "LinearPatternSourcePacket03" / "DisclosedNative"
    for name, rec in main["principal"].items():
        require(name[:4] in ("D01X", "D02Y"), "patterned principal disclosure list changed")
        yield principal / name[:4] / name, rec["sha256"], rec["placement"]
    for name, rec in main["oblique"].items():
        yield share / "LinearPatternEnvelope02" / "DisclosedTrial" / name, rec["sha256"], rec["placement"]
    for arm, rec in heights["cases"].items():
        yield share / "LinearPatternDatumHeight01" / "DisclosedHeights" / arm / rec["artifact"]["name"], rec["artifact"]["sha256"], rec["saved_display_formula"]


def verify_row(path, pin, source):
    model, roots, streams = replay(checked(path, pin))
    (pattern,) = [node for node in roots if isinstance(node, Obj) and node.cls == "moLPattern_c"]
    line = need_node(pattern["f1288"], "moLineRef_w")
    plane_ref = need_node(line["f58"], "moCompRefPlane_c")
    component = need_node(plane_ref["f58"], "moUnitComponent_c")
    require(line["f60"] is None and component["owner"] is model and component is not model["f990"]
            and line.index == source["direction_line_object"] and plane_ref["ff0"]["f00"] == source["plane_id"],
            "the selected direction is outside the observed independently allocated local part component")
    actual = {key: vector(line[key]) if key in ("fc8", "fe0") else line[key]
              for key in ("fc8", "fe0", "fb0", "fb8", "f68")}
    horizontal, _, normal = source["basis_u_v_n"]
    predicted = resolve_local_plane(source["display_origin_m"], horizontal, normal, source["ordered_borders_m"])
    actual_bytes = pack("<8dB", *actual["fc8"], *actual["fe0"], actual["fb0"], actual["fb8"], actual["f68"])
    predicted_bytes = pack("<8dB", *predicted["fc8"], *predicted["fe0"], predicted["fb0"], predicted["fb8"], predicted["f68"])
    require(actual_bytes == predicted_bytes, "ordered native arithmetic does not reproduce " + path.name)
    return {"native_file": path.name, "sha256": pin, "datum_class": source["plane_data_class"],
            "datum_id": source["plane_id"], "fields": predicted, "exact_binary64": True,
            "pattern_polarity_owner_f1298": pattern["f1298"], **streams}


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bindings = read_bindings(args.binaries)
    rows = [verify_row(path, pin, row) for path, pin, row in document_rows(args.disclosed_share)]
    require(len(rows) == 10 and len({row["sha256"] for row in rows}) == 10, "expected ten distinct disclosed snapshots")
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "pure host analysis imported a CAD runtime")
    result = {"schema": "kit.sw2026.linear-pattern-plane-direction-rule.v1", "static_native_bindings": bindings,
              "disclosed_cases": rows, "binding_source_sha256": [RECTANGLES, HEIGHTS],
              "arithmetic_sha256": digest(HERE.with_name("PatternPlaneDirectionRule.py").read_bytes()),
              "proof_sha256": digest(HERE.read_bytes()), "native_processes_started": 0,
              "hidden_inputs_read": 0, "cad_files_written": 0}
    with args.output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"receipt_sha256": digest(args.output.read_bytes()), "exact_disclosed_results": len(rows)}))


if __name__ == "__main__":
    main()
