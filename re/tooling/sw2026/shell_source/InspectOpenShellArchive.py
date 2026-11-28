import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

VERSION = 19000
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
KEYWORDS = "swXmlContents/KeyWords"
CASES = {
    "OpenShell.SLDPRT": ("73a4330ef831d38273ef6128bcbff15e4a105421219293ae5454941a3c7301cd", 0.0028),
    "OpenShellEdited.SLDPRT": ("c0be437a8c13a50c940b0d9cee51d369865abf3fa0a7ed62610fb9c76eb4b810", 0.00353),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def native_node(value, name):
    require(value is not None and value.cls == name and value.schema == 1, f"expected {name}")
    return value


def carrier_binding(reference, stock_id):
    carriers = []
    for item in reference["f10"]:
        surface = item["f08"]
        if surface is None:
            carriers.append(None)
            continue
        require(surface.cls in {"moEndFaceSurfIdRep_c", "moFromSktEntSurfIdRep_c"}, "unexpected native surface carrier")
        owner = native_node(surface["f10"]["f10"], "moFR_c")["f10"]
        require(owner["f00"] == stock_id, "shell selector does not bind the actual earlier stock")
        carriers.append({"class": surface.cls, "role": surface["f38"],
                         "stock": owner["f00"], "stock_event": owner["f08"]})
    require(reference["f08"] == len(carriers), "selector count differs")
    return {"index": reference.index, "carriers": carriers, "tag": reference["f70"],
            "trailer_mode": reference["fe8"], "field_span": [reference.pos, reference.end]}


def inspect_selectors(model, stock, shell, atom):
    marked = native_node(shell["f828"], "suObList")
    require(marked["n"] == len(marked["items"]) == 1, "uniform open shell requires one removed cap")
    face = native_node(marked["items"][0]["o"], "moCompFace_c")
    edge = native_node(shell["f848"], "moCompEdge_c")
    for item in (face, edge):
        unit = native_node(item["f58"], "moUnitComponent_c")
        require(unit["owner"] is model and not unit["has_ext"], "shell geometry selector must reference the local part")
        require(item["f18"] == item["f1c"] == atom["f140"], "shell geometry selector has inconsistent stock atom IDs")
    face_ref = carrier_binding(native_node(face["fe8"], "moFaceRef_c"), stock["f08"])
    edge_ref = carrier_binding(native_node(edge["fe8"], "moEdgeRef_c"), stock["f08"])
    face_modes = [(entry["class"], entry["role"]) for entry in face_ref["carriers"] if entry is not None]
    require(face_modes == [("moEndFaceSurfIdRep_c", 1), *[("moFromSktEntSurfIdRep_c", role) for role in (4, 1, 2, 3)]],
            "selected top cap lost its actual end or surrounding segment identities")
    require(face_ref["carriers"][-1] is None, "shell cap carrier lacks its terminal null")
    return {"removed_top_cap": face_ref, "auxiliary_edge": edge_ref,
            "face_component_index": face.index, "edge_component_index": edge.index}


def inspect_thickness(shell, thickness):
    display = native_node(shell["f818"], "moDisplayDistanceDim_c")
    require(display["n850"] == len(display["f850"]) == 1, "native shell display has no unique dimension handle")
    handle = native_node(display["f850"][0]["o"], "moFeatureDimHandle_c")
    kind = native_node(handle["ff0"], "ThreeDRadiusDim_c")
    for value in (display["fad0"], display["f988"]["x"], display["f9a0"]["x"]):
        require(math.isclose(value, thickness, rel_tol=4e-7, abs_tol=1e-12), "native display value differs from the edited thickness")
    return {"display_index": display.index, "display_class": display.cls, "handle_index": handle.index,
            "handle_value_kind": kind.cls, "dimension_number_rows": display["f2b0"],
            "value_m": display["fad0"], "point_m": display["f6a0"]["f38"],
            "display_axis": display["fa38"], "field_span": [display.pos, display.end]}


def inspect_file(path, expected, thickness):
    from Classes import registry
    from Core import Obj
    from RoundTrip import PLANS, one
    from defs.ConfigPart import load_config, store_config_state
    from defs.ResolvedCore import load_resolved, store_resolved
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Native import ParseXml

    raw = path.read_bytes()
    require(sha256(raw) == expected, "disclosed input changed")
    archive = SldprtArchive.from_bytes(raw, path.name)
    rules = registry()
    replay = one(str(path), None, rules, PLANS | rules.plans, linked=True, require_proven=True)
    require(replay["passed"] and len(replay["streams"]) == 15, "disclosed model stream replay is incomplete")
    configuration, config_map = load_config(archive.require(CONFIG), rules, VERSION, archive=archive, name=CONFIG)
    resolved, feature_map = load_resolved(archive.require(RESOLVED), rules, VERSION, archive=archive, name=RESOLVED,
                                         seed=config_map.map_state())
    config_bytes, seed = store_config_state(configuration, rules, VERSION)
    require(config_bytes == archive.require(CONFIG) and store_resolved(resolved, rules, VERSION, seed=seed) == archive.require(RESOLVED)
            and config_map.count == feature_map.base and not configuration.tail and not resolved.tail,
            "shell lost its actual inherited map or resolved stream bytes")
    model, = configuration.roots
    model = native_node(model, "moPart_c")
    roots = [value for value in resolved.roots if isinstance(value, Obj)]
    stock, shell = roots[-2:]
    native_node(stock, "moExtrusion_c")
    native_node(shell, "moShell_c")
    atom = native_node(shell["f538"], "moAtom_c")
    require(stock["f538"] is None and (atom["f12c"], atom["f130"]) == (stock["f08"], shell["f08"]),
            "solved shell atom lost its predecessor or producer")
    dense = open_document(raw, source_format="solidworks.sldprt", strict=True)
    operation, = (row for row in dense.feature_timeline if row.name == "OpenShell")
    known_parameter, = (row for row in dense.parameters if row.owner_id == operation.id)
    require(len(operation.selection_ids) == 2 and known_parameter.name == "D1",
            "legacy shell diagnostic needs an explicit comparison with typed selector")
    document_keywords = ParseXml(archive.require(KEYWORDS))
    raw_spans = {name: row["schema_usage"]["load"]["raw_operations"] for name, row in replay["streams"].items()
                 if row["schema_usage"]["load"]["raw_operations"]}
    require(shell["f820"] == 0 and all(native_node(shell[key], "suObList")["n"] == 0 for key in ("f830", "f838"))
            and shell["f850"] is None, "case leaves the measured one-cap uniform inward profile")
    require(sha256(path.read_bytes()) == expected, "source changed during read-only audit")
    return {
        "sha256": expected,
        "stream_replay": {name: {key: row[key] for key in ("sha256", "bytes", "map_base", "map_count", "tail")}
                          for name, row in replay["streams"].items()},
        "saved_raw_spans": raw_spans,
        "keywords": {"sha256": sha256(archive.require(KEYWORDS)), "root": document_keywords.tag},
        "archive_map": {"configuration_base": config_map.base, "resolved_base": feature_map.base,
                        "end": feature_map.count, "resolved_roots": len(roots)},
        "shell_identity": {"stock_id": stock["f08"], "shell_id": shell["f08"], "atom_id": atom["f140"],
                           "index": shell.index, "position": [shell.pos, shell.end], "atom_index": atom.index,
                           "event_tag": shell["f3c0"], "atom_event_tag": atom["f180"]},
        "shell_scope": {"direction_byte": shell["f820"], "f830_count": shell["f830"]["n"],
                        "f838_count": shell["f838"]["n"], "f850_is_null": True},
        "field_links": inspect_selectors(model, stock, shell, atom),
        "thickness_driver": inspect_thickness(shell, thickness),
        "legacy_sdk": {"selection_ids": operation.selection_ids, "parameter_id": known_parameter.id,
                       "parameter_role": known_parameter.role, "parameter_value_mm": known_parameter.value.value},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codecs", required=True, type=Path)
    parser.add_argument("--disclosure", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.codecs.resolve(strict=True)
    sys.path[:0] = [str(root / "re/tooling/sw2026/serial"), str(root / "src")]
    rows = {name: inspect_file(args.disclosure / name, expected, value)
            for name, (expected, value) in CASES.items()}
    result = {"schema": "kit-sw2026-open-shell-archive-observation-v1", "cases": rows,
              "paired_streams_exact": sum(len(row["stream_replay"]) for row in rows.values()),
              "heldout_inputs_read": 0, "generated_publications": 0}
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(result, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")


if __name__ == "__main__":
    main()
