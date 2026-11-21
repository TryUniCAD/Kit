from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from Classes import registry
from RoundTrip import PLANS, stream_roundtrip
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved

from convert.adapters.solidworks.Container.Container import SldprtArchive


CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
STREAMS = ("Contents/CMgr", "Contents/CMgrHdr2", CONFIG, CONFIG + "-ModelHeader", RESOLVED,
           "Contents/Definition", "Header2")
KINDS = ("corner", "center")
ROLES = ("Original", "WidthEdit", "HeightEdit")
ORACLE_SHA = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def checked(path, expected):
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"file changed: {path.name}")
    return data


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire_graph(archive, rules, kind):
    config, prior = load_config(archive.require(CONFIG), rules, 19000, archive=archive, name=CONFIG)
    resolved, after = load_resolved(archive.require(RESOLVED), rules, 19000, archive=archive, name=RESOLVED,
                                    seed=prior.map_state())
    origin, = (feature for feature in resolved.roots if feature.cls == "moOriginProfileFeature_c")
    profile, = (feature for feature in resolved.roots if feature.cls == "moProfileFeature_c")
    sketch = profile["pd_f80"]
    dims = sketch["dims"]
    external_slot, external = next((i, row["point"]) for i, row in enumerate(sketch["points"]) if row["kind"] == 1)
    require(sum(row["kind"] == 1 for row in sketch["points"]) == 1, "unexpected additional external point")
    wrapper = external["ext"]["f08"]
    owner = wrapper["f58"]
    point = owner["f0f8"]
    require(external["ext"].cls == "sgExtEnt_c" and wrapper.cls == "moSketchExtRef_w" and
            owner.cls == "moCompSketchEntHandle_c" and point.cls == "sgPointHandle" and
            owner["ff0"]["f00"] == origin["f08"] and point["idx"] == 0 and
            origin["pd_f80"]["npoints"] == 1 and wrapper["fb8"].cls == "moPointBackedUpData_c",
            "external point must target the actual origin profile and point")
    pair_rows = [row["d"] for row in dims["log_g2"]]
    count = 1 if kind == "corner" else 3
    require(len(pair_rows) == count and all(row["f80"] == 9 for row in pair_rows) and
            dims["ng2"] == 2 and dims["nlog1"] == 4 and sketch["f188"] == 0,
            "native rectangle constraint owners differ")
    binding = [(row["h1"]["idx"], row["h1"].cls, row["h2"]["idx"], row["h2"].cls) for row in pair_rows]
    foreign, local_kind, local, target_kind = binding[-1]
    require(foreign == external_slot and local_kind == target_kind == "sgPointHandle" and
            0 <= local < sketch["npoints"] and sketch["points"][local]["kind"] == 0,
            "origin coincidence lost its local/external point pair")
    require(external["pos"] == sketch["points"][local]["point"]["pos"] == {"x": 0.0, "y": 0.0},
            "anchored local and external points must coincide at the origin")
    if kind == "center":
        require(all(item[0] == local and item[1] == "sgPointHandle" and item[3] == "sgLineHandle" for item in binding[:-1])
                and len({item[2] for item in binding[:-1]}) == 2, "center point must own both diagonal coincidences")
    return {"origin_feature_id": origin["f08"], "sketch_feature_id": profile["f08"], "external_point_owner": external["ext"].cls,
            "external_reference_wrapper": wrapper.cls, "referenced_feature_id": owner["ff0"]["f00"],
            "referenced_feature_stamp": owner["ff0"]["f08"], "referenced_point_slot": point["idx"],
            "referenced_point_mark": owner["f100"], "backup_point": wrapper["fb8"].cls,
            "external_point_local_slot": external_slot, "anchored_local_point_slot": local,
            "component_class": owner["f58"].cls, "component_reuses_config_self": owner["f58"] is config.roots[0]["f990"],
            "coincidence_bindings": binding, "sketch_external_reference_state": sketch["f188"],
            "config_terminal_map": prior.count, "resolved_terminal_map": after.count}


def audit(root, source_sha, native_sha, host_sha):
    result_root = root / "RectangleAnchorResults"
    source = json.loads(checked(root / "Source.json", source_sha))
    result = json.loads(checked(result_root / "Result.json", native_sha))
    host = json.loads(checked(root / "AnchorSourceHost01.json", host_sha))
    require(source["schema"] == result["schema"] == "kit.sw2026.rectangle-anchor-source.v1" and
            source["oracle_sha256"] == ORACLE_SHA and result["job_sha256"] == source_sha and
            result["source_measurement_passed"] and result["controls_healthy"] and result["distinct_processes"] == 6 and
            result["writer_output_count"] == result["heldout_inputs_tested"] == 0 and
            host["transport_returncode"] == host["supervisor_exit_code"] == 0, "unqualified disclosed native source run")
    require(tuple(result["cases"]) == KINDS, "disclosed native source cases differ")
    for filename, expected in source["tools_sha256"].items():
        checked(root / "Tools" / filename, expected)
    checked(root / "Control.SLDPRT", source["control_sha256"])
    rules = registry()
    phases, pairs, cases = [], set(), {}

    def record(name, item):
        raw = json.loads(checked(result_root / name / "Record.json", item["record_sha256"]))
        identity = item["oracle_identity"]
        pair = (identity["process_id"], identity["process_creation_filetime"])
        require(identity["version_matches"] and identity["sha256"] == ORACLE_SHA and pair not in pairs and item["passed"],
                "native phase identity or verdict differs")
        pairs.add(pair)
        sampled = host["progress"]["records"].get(name + "/Record.json", {})
        checks = raw.get("checks", [])
        require(all(row["passed"] for row in checks), "native numeric check failed")
        phases.append({"phase": name, "process_id": pair[0], "creation_filetime": pair[1], "record_sha256": item["record_sha256"],
                       "host_sample_matches_terminal": sampled.get("sha256") == item["record_sha256"], "numeric_checks": len(checks)})

    record("ControlBefore", result["control_before"])
    for kind, case in result["cases"].items():
        authored, reopened = case["author"], case["reopen"]
        record(kind + "/Author", authored)
        record(kind + "/Reopen", reopened)
        cases[kind] = []
        for role in ROLES:
            native = authored["files"][role]
            raw = checked(result_root / kind / "Author" / (role + ".SLDPRT"), native["sha256"])
            check = reopened["files"][role]
            observations = reopened["observed"][role]
            require(check["open_errors"] == check["open_warnings"] == 0 and native["status"] == [True, 0, 0] and
                    len(raw) == native["bytes"] and observations["constraint_status"] == 3 and observations["body_count"] == 1,
                    "native rectangle save, fresh load or constraint verdict differs")
            require(observations["tree"] == authored["observed"][role]["tree"] and
                    observations["relations"] == authored["observed"][role]["relations"], "native anchored profile identity changed")
            archive = SldprtArchive.from_bytes(raw)
            streams = {name: stream_roundtrip(archive, name, rules, {**PLANS, **rules.plans}, linked=True) for name in STREAMS}
            require(all(row["passed"] for row in streams.values()), "native source linked stream failed byte comparison")
            cases[kind].append({"role": role, "file_sha256": native["sha256"], "file_bytes": native["bytes"],
                                "streams": {name: {"bytes": len(archive.require(name)), "sha256": sha256(archive.require(name)).hexdigest()}
                                            for name in STREAMS},
                                "wire": wire_graph(archive, rules, kind), "mass_properties": observations["mass_properties"],
                                "relations": observations["relations"], "dimensions_m": observations["dimensions_m"],
                                "native_full_constraint": True, "open_errors": 0, "open_warnings": 0})
    record("ControlAfter", result["control_after"])
    return {"schema": "kit.sw2026.rectangle-anchor-source-measurement.v1", "source_commit": source["source_commit"],
            "source_job_sha256": source_sha, "source_tools_sha256": source["tools_sha256"], "native_report_sha256": native_sha,
            "host_supervisor_sha256": host_sha, "oracle_sha256": ORACLE_SHA, "oracle_file_version": "34.5.2.0604",
            "phases": phases, "native_processes": len(phases), "native_numeric_checks": sum(row["numeric_checks"] for row in phases),
            "exact_stream_checks": len(STREAMS) * sum(len(rows) for rows in cases.values()), "cases": cases,
            "heldout_inputs_tested": 0, "writer_output_count": 0, "native_acceptance": False}


def main():
    parser = argparse.ArgumentParser(description="Audit disclosed corner and center rectangle native source siblings")
    parser.add_argument("root", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--host-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root, args.source_sha256, args.native_sha256, args.host_sha256)
    with args.report.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(report["native_processes"], report["native_numeric_checks"], report["exact_stream_checks"])


if __name__ == "__main__":
    main()
