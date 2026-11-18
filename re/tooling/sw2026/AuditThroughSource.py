import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import platform


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run(command, folder, data=None, expect_success=True):
    folder.mkdir(parents=True, exist_ok=False)
    result = subprocess.run(
        command,
        input=None if data is None else json.dumps(data),
        text=True,
        capture_output=True,
    )
    (folder / "Stdout.txt").write_text(result.stdout)
    (folder / "Stderr.txt").write_text(result.stderr)
    receipt = {
        "exit_code": result.returncode,
        "stdout_sha256": digest(folder / "Stdout.txt"),
        "stderr_sha256": digest(folder / "Stderr.txt"),
    }
    (folder / "Process.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if (result.returncode == 0) != expect_success:
        raise ValueError(
            "process outcome differs from declared expectation: " + str(folder)
        )
    return receipt


def mutations(document):
    definitions = document["feature_timeline"]["$tuple"]
    boss = next(
        index
        for index, value in enumerate(definitions)
        if value["operation"] and value["operation"]["value"] == "join"
    )
    cut = next(
        index
        for index, value in enumerate(definitions)
        if value["operation"] and value["operation"]["value"] == "cut"
    )
    for label in (
        "MissingStockSelection",
        "ForeignStockProducer",
        "MissingCentrePoint",
        "ExtraCentrePoint",
        "UnusedCutLength",
        "LostAxisRelation",
        "ForeignDirectionAxis",
    ):
        data = deepcopy(document)
        rows = data["feature_timeline"]["$tuple"]
        sketches = data["sketches"]["$tuple"]
        selections = data["selections"]["$tuple"]
        if label == "MissingStockSelection":
            rows[cut]["selection_ids"] = {"$tuple": []}
        elif label == "ForeignStockProducer":
            value = next(
                value
                for value in selections
                if value["id"] in rows[cut]["selection_ids"]["$tuple"]
            )
            value["path"]["$tuple"][0]["entity_id"] = rows[cut]["id"]
        elif label == "MissingCentrePoint":
            sketches[1]["entities"]["$tuple"] = [
                value
                for value in sketches[1]["entities"]["$tuple"]
                if value["geometry"]["$type"] != "PointGeometry"
            ]
        elif label == "ExtraCentrePoint":
            value = deepcopy(
                next(
                    value
                    for value in sketches[1]["entities"]["$tuple"]
                    if value["geometry"]["$type"] == "PointGeometry"
                )
            )
            value["id"] += ":independent"
            sketches[1]["entities"]["$tuple"].append(value)
        elif label == "UnusedCutLength":
            rows[cut]["definition"]["length"] = deepcopy(
                rows[boss]["definition"]["length"]
            )
        elif label == "LostAxisRelation":
            sketches[0]["constraints"]["$tuple"].pop()
        elif label == "ForeignDirectionAxis":
            value = next(
                value
                for value in selections
                if value["query"].get("topology_role") == "direction_axis"
            )
            value["path"]["$tuple"][0]["entity_id"] = "ForeignSketch"
        yield label, data


def check(args):
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    cohort = json.loads(args.cohort.read_text())
    source_manifest = json.loads(args.reader_manifest.read_text())
    method_manifest = json.loads(args.method_manifest.read_text())
    for name, expected in method_manifest["files_sha256"].items():
        if digest(Path(__file__).parent / name) != expected:
            raise ValueError("frozen method source changed: " + name)
    for name, expected in source_manifest["files_sha256"].items():
        if digest(args.root / name) != expected:
            raise ValueError("pinned reader source changed: " + name)
    tool_root = Path(__file__).parent / "throughsource"
    reader, worker = tool_root / "ReadSource.py", tool_root / "Process.py"
    results, process_count = [], 0
    for item in cohort["cases"]:
        label = item["id"]
        trial_file = Path(item["trial"])
        if digest(trial_file) != item["trial_sha256"]:
            raise ValueError("declared trial custody changed")
        trial = json.loads(trial_file.read_text())
        control_key = trial["control_file"]
        expected = trial["files_sha256"][control_key]
        source = trial_file.parent / control_key
        if expected != item["source_sha256"] or digest(source) != expected:
            raise ValueError("disclosed control identity changed")
        base = output / label
        base.mkdir()
        read_args = [
            sys.executable,
            "-B",
            str(reader),
            "--root",
            str(args.root),
            "--source",
            str(source),
            "--source-sha256",
            expected,
            "--output",
            str(base / "Read"),
        ]
        run(read_args, base / "ReaderProcess")
        process_count += 1
        audits = []
        for mode in ("ordinary", "parametric"):
            data = json.loads((base / "Read" / (mode + ".json")).read_text())
            command = [
                sys.executable,
                "-B",
                str(worker),
                "--root",
                str(args.root),
                "--output",
                str(base / (mode + "Audit")),
            ]
            run(command, base / (mode + "Process"), data)
            process_count += 1
            audits.append(
                json.loads((base / (mode + "Audit") / "Result.json").read_text())
            )
        first = json.loads((base / "ordinaryAudit" / "Prediction.json").read_text())
        second = json.loads((base / "parametricAudit" / "Prediction.json").read_text())
        if first != second:
            raise ValueError("cache inclusion changed the portable prediction")
        source_data = json.loads((base / "Read" / "ordinary.json").read_text())
        negative_results = []
        for name, data in mutations(source_data):
            command = [
                sys.executable,
                "-B",
                str(worker),
                "--root",
                str(args.root),
                "--output",
                str(base / "Rejected" / name),
            ]
            result = run(command, base / "NegativeProcesses" / name, data, False)
            process_count += 1
            negative_results.append({"name": name, "exit_code": result["exit_code"]})
        altered = deepcopy(source_data)
        removed = altered["feature_timeline"]["$tuple"].pop(0)
        for row in altered["feature_timeline"]["$tuple"]:
            row["order"] -= 1
        comparison = [
            sys.executable,
            "-B",
            str(worker),
            "--root",
            str(args.root),
            "--output",
            str(base / "MissingHistoryComparison"),
            "--compare",
        ]
        run(
            comparison,
            base / "HistoryComparisonProcess",
            {"source": source_data, "candidate": altered},
        )
        process_count += 1
        actual = json.loads(
            (base / "MissingHistoryComparison" / "Result.json").read_text()
        )
        if (
            actual["ordered_portable_history_equal"]
            or actual["full_original_equivalence"]
            or not actual["shape_equal"]
        ):
            raise ValueError(
                "stripped history incorrectly qualified or changed independent geometry"
            )
        results.append(
            {
                "id": label,
                "source_sha256": expected,
                "trial_sha256": item["trial_sha256"],
                "audits": audits,
                "prediction_equal_with_and_without_brep": True,
                "rejected_shape_inputs": negative_results,
                "removed_history_owner_detected": removed["id"],
                "stripped_shape_never_certified": True,
                "signed_prediction": first,
                "coverage_sha256": digest(base / "ordinaryAudit" / "Coverage.json"),
            }
        )
        if digest(source) != expected:
            raise ValueError("source changed during read-only audit")
    receipt = {
        "status": "passed_source_audit_not_conversion",
        "reader_revision": source_manifest["source_revision"],
        "reader_manifest_sha256": digest(args.reader_manifest),
        "method_manifest_sha256": digest(args.method_manifest),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "executable_sha256": digest(Path(sys.executable)),
        },
        "cohort_sha256": digest(args.cohort),
        "fresh_process_count": process_count,
        "cases": results,
        "native_oracle_used": False,
        "writer_output_count": 0,
        "held_out_accessed": False,
        "native_acceptance": False,
        "full_original_source_equivalence": False,
    }
    (output / "Result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "fresh_process_count": process_count,
                "cases": len(results),
                "result_sha256": digest(output / "Result.json"),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--reader-manifest", type=Path, required=True)
    parser.add_argument("--method-manifest", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    check(parser.parse_args())


if __name__ == "__main__":
    main()
