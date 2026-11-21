from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parents[1]))
sys.path.insert(0, str(SCRIPT.parents[4] / "src"))

from AuthorCurves import digest, require
from Classes import registry
from Core import Obj
from NestedAssemblySourcePlan import ORACLE, checked
from RoundTrip import PLANS, stream_roundtrip, usage_summary
from SyncedAssemblies import typed_header
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


PACKET_SHA = "efc1cae76b8c7b0b6c0a9913e759248e32aa5ac4a15f0591a11aefd798dded53"
RESULT_SHA = "539cb901df420671788475640ad5f097d673c48027a2754bea1e01396e908158"
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
HEADER = CONFIG + "-ModelHeader"
CMGR = "Contents/CMgr"
SUMMARY = "Contents/CMgrHdr2"
STREAMS = (CONFIG, RESOLVED, CMGR, SUMMARY, HEADER, "Header2")


def box_words(box):
    return struct.pack("<10d", *(box[f"b{i}"] for i in range(10)))


def projection(path, identity, reg):
    checked(path, identity["sha256"], path.parent)
    require(path.stat().st_size == identity["bytes"], "generated trial file size differs from its locked measurement")
    archive = SldprtArchive.from_bytes(path.read_bytes(), path)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000, "unexpected generated native archive release")
    reports = {stream: stream_roundtrip(archive, stream, reg, {**PLANS, **reg.plans}, linked=True) for stream in STREAMS}
    require(all(row["passed"] for row in reports.values()), "generated native save has an incomplete scoped codec")
    config, config_map = load_config(archive.require(CONFIG), reg, 19000, archive=archive)
    resolved, resolved_map = load_resolved(archive.require(RESOLVED), reg, 19000, archive=archive, name=RESOLVED, seed=config_map.map_state())
    replay, map_state = store_config_state(config, reg, 19000)
    require(replay == archive.require(CONFIG) and store_resolved(resolved, reg, 19000, seed=map_state) == archive.require(RESOLVED),
            "generated native save loses its continuous configuration map")
    model, = config.roots
    header = config.head["model_header"]
    top = typed_header(archive, reg, "Header2", "moHeader_c")
    manager = typed_header(archive, reg, CMGR, "moConfigurationMgr_c")
    summary = typed_header(archive, reg, SUMMARY, "dmConfigMgrHeader_c")
    row, = summary["f08"]["items"]
    config_header = row["o"]
    require(manager["f360"]["f860"] == config_header["f38"] == header["f40"] == top["f40"], "saved configuration and header update stamps differ")
    refs = [row["o"] for row in model["f68"]["list"]["items"]] if model.cls == "moAssembly_c" else []
    slots = {id(row[1]): index for index, row in config_map.table.items() if row[0] == "obj"}
    require(all(resolved_map.table[slots[id(ref)]][1] is ref for ref in refs), "resolved map changes direct occurrence identity")
    state = {"sha256": identity["sha256"], "bytes": identity["bytes"], "class": model.cls,
             "activity_count": manager["f360"]["f4b0"], "f1300_geometry_stamp": model["f1300"],
             "config_header_geometry_stamp": config_header["f50"] & 0xFFFFFFFF,
             "config_header_transform_stamp": config_header["f4c"] & 0xFFFFFFFF,
             "headers": {name: {key: node[key] for key in ("fc4", "f40", "f48")} for name, node in ((HEADER, header), ("Header2", top))},
             "self_file_time": header["f38"]["f60"], "manager_save_time": summary["f60"],
             "resolved_roots": [{"class": node.cls, "id": node["f08"]} for node in resolved.roots if isinstance(node, Obj)],
             "streams": {name: {key: row[key] for key in ("sha256", "bytes", "map_base", "map_count", "tail")} |
                         {"schema_usage": {phase: {"provisional": data["provisional_schemas"], "raw_operations": data["raw_operation_count"]}
                                           for phase, data in usage_summary([row]).items()}} for name, row in reports.items()}}
    if model.cls == "moPart_c":
        extrusion, = [node for node in resolved.roots if isinstance(node, Obj) and node.cls == "moExtrusion_c"]
        end = extrusion["f818"]
        require((end["f08"], end["f0c"], end["f8c"]) == (1, 0, 0), "persisted edited leaf is outside the forward blind profile")
        state["end_spec"] = {"directions": end["f08"], "condition": end["f0c"], "reverse": end["f8c"],
                             "active_depth_m": end["f18"]["f850"][0]["o"]["ff0"]["f28"]["f58"],
                             "inactive_depth_m": end["f20"]["f850"][0]["o"]["ff0"]["f28"]["f58"]}
    else:
        state["direct_count"] = model["f1560"]
        state["references"] = [{"name": ref["f18"]["f08"], "target": ref["f3b0"]["shared"]["h10"]["f08"], "id": ref["f08"],
                                "directory_slot": slots[id(ref["f3b0"])], "directory_uses": ref["f3b0"]["f48"], "child_kind": ref["f3b0"]["shared"]["f20"],
                                "stamps": {key: ref[key] for key in ("f3e0", "f3e8", "f3f0", "f3f4", "f3f8")}} for ref in refs]
        state["configuration_order"] = [row["o"]["f10"]["f20"]["f08"]["f08"][0]["o"]["f44"] for row in manager["f360"]["fce8"][1:]]
        require(state["configuration_order"] == [ref["f08"] for ref in reversed(refs)], "saved CMgr direct occurrence order differs")
    return {"model": model, "header": header, "summary": summary, "refs": refs, "state": state}


def validate_targets(documents, prediction, edited):
    by_name = {row["model"]["f18"]["f08"]: row for row in documents.values()}
    for key, document in documents.items():
        geometry, transform = document["model"]["f1300"], 101
        for reference, state in zip(document["refs"], document["state"].get("references", ()), strict=True):
            child = by_name[state["target"]]
            expected = child["state"]
            require((reference["f3e0"], reference["f3e8"], reference["f3f4"], reference["f3f8"]) ==
                    (child["header"]["f40"], child["header"]["f48"], expected["config_header_geometry_stamp"], expected["config_header_transform_stamp"]),
                    "persisted reference target state differs from its actual saved dependency")
            require(reference["f3b0"]["f60"] == child["header"]["f38"]["f60"] and reference["f3b0"]["f70"] == child["summary"]["f60"],
                    "persisted directory times differ from their target owners")
            if edited:
                child_box = child["model"]["f1a18" if child["model"].cls == "moAssembly_c" else "f7f8"]
                state["target_local_bounds_byte_equal"] = box_words(reference["f370"]) == box_words(child_box)
            geometry = (geometry + reference["f3f4"]) & 0xFFFFFFFF
            transform = reference["f3f0"] if transform == 101 else (transform + reference["f3f0"]) & 0xFFFFFFFF
        require((geometry, transform) == (document["state"]["config_header_geometry_stamp"], document["state"]["config_header_transform_stamp"]),
                "persisted recursive stamp formulas differ from CMgrHdr2")
        if document["model"].cls == "moPart_c":
            expected_depth = prediction["definitions"][key]["edited" if edited else "initial"]["dimensions_m"]["D1@Boss-Extrude1"]
            require(document["state"]["end_spec"]["active_depth_m"] == expected_depth, "typed saved depth differs from its native measured edit")


def main():
    parser = argparse.ArgumentParser(description="Audit the original generated nested trial and its exact native saved derivatives")
    parser.add_argument("trial", type=Path)
    args = parser.parse_args()
    root = args.trial.resolve(strict=True)
    require(root.name == "GeneratedNestedAssembly01", "use the exact disclosed generated trial")
    packet = json.loads(checked(root / "Trial.json", PACKET_SHA, root).read_bytes())
    result = json.loads(checked(root / "Inspection/NestedAssemblyResults.json", RESULT_SHA, root).read_bytes())
    prediction = json.loads(checked(root / "Expected.json", packet["prediction_sha256"], root).read_bytes())
    require(result["passed"] and result["controls_healthy"] and result["distinct_processes"] == 4 and result["oracle_sha256"] == ORACLE and
            result["packet_sha256"] == PACKET_SHA and result["heldout_inputs_read"] == 0, "disclosed native trial is not qualified")
    saved = result["phases"][1]["saved_files"]
    reopened = result["phases"][2]["initial"]["definitions"]
    require(set(saved) == set(packet["files"]) == set(reopened) and all(row["status"] == [True, 0, 0] and
            row["sha256"] == reopened[key]["sha256"] for key, row in saved.items()), "native derivative closure differs from save and reopen observations")
    reg = registry()
    reports = {}
    for role, edited in (("FrozenGenerated", False), ("GeneratedInput", True)):
        files = saved if edited else packet["files"]
        documents = {key: projection(root / role / packet["files"][key]["file"], value, reg) for key, value in files.items()}
        validate_targets(documents, prediction, edited)
        reports[role] = {key: document["state"] for key, document in documents.items()}
    report = {"schema": "kit.sw2026.generated-nested-save-typed-audit.v1", "tool_sha256": digest(SCRIPT), "packet_sha256": PACKET_SHA,
              "raw_native_result_sha256": RESULT_SHA, "writer_revision": result["writer_revision"], "typed_audit_passed": True,
              "stream_round_trips": sum(len(document["streams"]) for role in reports.values() for document in role.values()),
              "heldout_inputs_read": 0, "native_files_written": 0, "documents": reports}
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
