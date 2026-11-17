import argparse
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parents[1]))
sys.path.insert(0, str(SCRIPT.parents[4] / "src"))

import AuditReferencePlaneSources as Sources
from ReferencePlaneCompatibilityRead import project_face_offset


def project(path, identity, case, edited, snapshot):
    rules = Sources.registry()
    raw = path.read_bytes()
    Sources.require(Sources.digest(path) == identity["sha256"] and len(raw) == identity["bytes"], "source changed before compatibility readback")
    archive = Sources.SldprtArchive.from_bytes(raw, path)
    Sources.require(archive.format_version == 4 and Sources.ContainerMo(archive.streams) == 19000,
                    "compatibility source audit requires native container 4 / model 19000")
    streams = Sources.stream_reports(archive, rules)
    result = {"sha256": identity["sha256"], "bytes": identity["bytes"], "streams": streams, "passed": False}
    if not all(row["passed"] for row in streams.values()):
        result["error"] = "one or more scoped stream codecs failed exact consumption or byte identity"
        return result
    configuration, config_map = Sources.load_config(archive.require(Sources.CONFIG), rules, 19000, archive=archive, name=Sources.CONFIG)
    resolved, resolved_map = Sources.load_resolved(archive.require(Sources.RESOLVED), rules, 19000, archive=archive, name=Sources.RESOLVED, seed=config_map.map_state())
    Sources.require(not configuration.tail and not resolved.tail and resolved_map.base == config_map.count,
                    "source configuration and resolved graph lose their shared object map")
    config_bytes, seed = Sources.store_config_state(configuration, rules, 19000)
    Sources.require(config_bytes == archive.require(Sources.CONFIG) and Sources.store_resolved(resolved, rules, 19000, seed=seed) == archive.require(Sources.RESOLVED),
                    "compatibility source loses its re-emitted configuration seed")
    model, = configuration.roots
    result["projection"] = project_face_offset(model, resolved.roots, resolved_map, case, Sources.geometry(case, edited), snapshot)
    result["passed"] = result["projection"]["passed"]
    result["map"] = {"config_base": config_map.base, "config_count": config_map.count, "resolved_base": resolved_map.base,
                     "resolved_count": resolved_map.count, "context": resolved.head["context"], "re_emitted_seed_continuity": True}
    Sources.require(path.read_bytes() == raw, "compatibility audit changed an immutable native source")
    return result


def audit(root, packet_sha, case):
    saved, paths, qualification = Sources.qualified_case(root, packet_sha, case)
    result = {"case_id": case["id"], "source_qualification": qualification, "siblings": {}, "passed": False}
    for role, edited in (("source", False), ("edited", True)):
        identity = saved["result"]["saved_files"][role]
        try:
            result["siblings"][role] = project(paths[role], identity, case, edited, saved["result"]["edited" if edited else "initial"])
        except Exception as error:
            result["siblings"][role] = {"sha256": identity["sha256"], "passed": False, "error": repr(error)}
    result["passed"] = all(row["passed"] for row in result["siblings"].values())
    if result["passed"]:
        original, edited = (result["siblings"][role]["projection"] for role in ("source", "edited"))
        result["edit_checks"] = {
            "plane_feature_identity_preserved": original["plane_feature_id"] == edited["plane_feature_id"],
            "distance_dimension_identity_preserved": original["distance_graph"]["dimension_persistent_id"] == edited["distance_graph"]["dimension_persistent_id"],
            "selected_principal_preserved": original["support_feature_id"] == edited["support_feature_id"],
            "declared_distance_changed": original["distance_m"] != edited["distance_m"],
            "stored_origin_changed": original["common_origin_m"] != edited["common_origin_m"],
            "boss_depth_preserved": original["boss_depth_m"] == edited["boss_depth_m"],
        }
        result["passed"] = all(result["edit_checks"].values())
    for role, path in paths.items():
        Sources.checked(path, saved["result"]["saved_files"][role]["sha256"], path.parent)
    result["source_assets_unchanged"] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--case", choices=Sources.DISCLOSED, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    Sources.require(len(set(args.case)) == len(args.case), "duplicate disclosed source case")
    custody = Sources.DisclosedReads(args.packet, args.case)
    sys.addaudithook(custody.observe)
    root, packet = Sources.source_packet(args.packet, args.packet_sha256)
    Sources.require(args.output.is_absolute() and args.output.parent.resolve(strict=True) == args.output.parent and not args.output.exists() and
                    not args.output.is_relative_to(root), "choose an unused absolute compatibility receipt outside the source packet")
    declared = {row["id"]: row for row in Sources.disclosed_cases()}
    result = {"schema": "kit.sw2026.disclosed-face-offset-audit.v1", "source_packet_sha256": args.packet_sha256,
              "cases": [audit(root, args.packet_sha256, declared[name]) for name in args.case], "writer_output_count": 0,
              "heldout_inputs_read": 0, "native_processes_started": 0, "generated_native_acceptance": False,
              "cache_formulas_and_neutral_states_qualified": False}
    result["passed"] = all(row["passed"] for row in result["cases"])
    result["source_read_custody"] = custody.report()
    result["code_fingerprints"] = Sources.source_fingerprints()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": Sources.digest(args.output), "passed": result["passed"], "heldout_inputs_read": 0, "writer_output_count": 0}))
    raise SystemExit(0 if result["passed"] else 3)


if __name__ == "__main__":
    main()
