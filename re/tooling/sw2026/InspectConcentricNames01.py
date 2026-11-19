import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import InspectConcentricOpenDiagnostic01 as original

ROLES = ("ControlBefore", "ParentRebuild", "ControlAfter")
CAPTURE = original.baseline.capture


def names(author, model, child_path):
    result = []
    feature = author.get(model, "FirstFeature")
    visited = 0
    while feature is not None:
        visited += 1
        original.baseline.require(
            visited <= 512, "reference-name traversal exceeded its ordinary scope"
        )
        kind = str(author.get(feature, "GetTypeName2"))
        if kind == "Reference":
            row = {
                "feature_id": int(author.get(feature, "GetID")),
                "feature_name": str(author.get(feature, "Name")),
                "feature_type": kind,
            }
            specific = author.get(feature, "GetSpecificFeature2")
            row["specific_nonnull"] = specific is not None
            if specific is not None:
                component = author.typed(specific, "Component2")
                row.update(
                    component_id=int(author.get(component, "GetID")),
                    component_name2=str(author.get(component, "Name2")),
                    component_path=str(author.get(component, "GetPathName")),
                )
                row["feature_id_equals_component_id"] = (
                    row["feature_id"] == row["component_id"]
                )
                row["component_path_matches_actual_child"] = (
                    original.baseline.same_file(row["component_path"], child_path)
                )
                row["repeated_component_read_stable"] = (
                    row["component_id"],
                    row["component_name2"],
                ) == (
                    int(author.get(component, "GetID")),
                    str(author.get(component, "Name2")),
                )
            row["repeated_feature_read_stable"] = (
                row["feature_id"],
                row["feature_name"],
            ) == (int(author.get(feature, "GetID")), str(author.get(feature, "Name")))
            result.append(row)
        feature = author.get(feature, "GetNextFeature")
    valid = (
        len(result) == 2
        and all(
            row["specific_nonnull"]
            and row.get("repeated_component_read_stable")
            and row["repeated_feature_read_stable"]
            for row in result
        )
        and len({row.get("component_id") for row in result}) == 2
    )
    return {
        "references": result,
        "top_level_features_visited": visited,
        "observation_complete": valid,
    }


def capture(author, model, assembly, child_path, prediction, edited=False):
    row = {
        "expected_occurrence_names": [
            value["name"] for value in prediction["occurrences"]
        ],
        "edited": edited,
    }
    try:
        row.update(names(author, model, child_path))
    except Exception as error:
        row.update(
            observation_complete=False,
            error={"type": type(error).__name__, "error": str(error)},
        )
    author.rec.data.setdefault("reference_name_observations", []).append(row)
    author.rec.flush()
    return CAPTURE(author, model, assembly, child_path, prediction, edited)


original.baseline.capture = capture
original.ROLES = ROLES


def verify(path, expected):
    config, job = original.verify(path, expected)
    original.baseline.require(
        config.get("name_probe_schema")
        == "kit.sw2026.concentric-reference-name-probe.v1"
        and config["roles"] == list(ROLES),
        "unexpected name discriminator scope",
    )
    for relative, digest in config["name_files_sha256"].items():
        original.baseline.checked(path.parent / relative, digest)
    return config, job


def phase(path, expected, role):
    verify(path, expected)
    result = original.phase(path, expected, role)
    record_path = path.parent / "Inspection" / "Feature" / role / "Record.json"
    raw = json.loads(record_path.read_bytes())
    observations = raw.get("reference_name_observations", [])
    complete = bool(
        result.get("diagnostic_completed")
        and len(observations) == 2
        and all(row.get("observation_complete") for row in observations)
    )
    result.update(
        name_probe_completed=complete,
        reference_name_observations=observations,
        native_acceptance=False,
    )
    original.baseline.write_json(
        path.parent / "Inspection" / "Feature" / role / "NameResult.json", result
    )
    return result


def summary(path, expected):
    verify(path, expected)
    rows = {}
    for role in ROLES:
        record = path.parent / "Inspection" / "Feature" / role / "NameResult.json"
        if record.is_file():
            rows[role] = json.loads(record.read_bytes())
    identities = {
        (row.get("oracle_identity") or {}).get("process_creation_filetime")
        for row in rows.values()
    } - {None}
    healthy = all(
        rows.get(role, {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    result = {
        "schema": "kit.sw2026.concentric-reference-name-result.v1",
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "name_probe_completed": bool(
            healthy
            and len(identities) == len(rows) == 3
            and all(row.get("name_probe_completed") for row in rows.values())
        ),
        "phases": rows,
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "file_saves": 0,
        "parameter_edits": 0,
        "global_preference_changes": 0,
    }
    original.baseline.write_json(path.parent / "NameResult.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--role", choices=ROLES)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.sha256)
        print(
            json.dumps(
                {
                    "verified": True,
                    "native_processes_started": 0,
                    "heldout_inputs_read": 0,
                }
            )
        )
        return 0
    result = (
        phase(path, args.sha256, args.role)
        if args.command == "phase"
        else summary(path, args.sha256)
    )
    print(
        json.dumps(
            {
                "name_probe_completed": result["name_probe_completed"],
                "native_acceptance": False,
            }
        )
    )
    return 0 if result["name_probe_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
