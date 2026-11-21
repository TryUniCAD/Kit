import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(manifest_path, actual_root):
    value = json.loads(manifest_path.read_bytes())
    expected = {row["path"] for row in value["files"]}
    actual = {str(path.relative_to(actual_root)) for path in actual_root.rglob("*") if path.is_file()}
    require(actual == expected, "frozen source or tool membership differs")
    for row in value["files"]:
        path = actual_root / row["path"]
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "frozen file differs: " + row["path"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "chronology proof output must be unused")
    verify(root / "Source01.json", root / "Code01")
    verify(root / "BaselineSource02.json", root / "Baseline01")
    verify(root / "Tools03.json", root / "Tools03")
    inputs_path = root / "Inputs01.json"
    expected_inputs = "9df7ffdfa513226e453a29d87a0e855a13e8fe6a23ac383c03ce5227afd9dee3"
    require(digest(inputs_path) == expected_inputs, "disclosed source and neutral input manifest changed")
    inputs = json.loads(inputs_path.read_bytes())
    require(inputs["heldout_inputs_read"] == 0 and len(inputs["sources"]) == 4 and len(inputs["generated_requests"]) == 4, "chronology trial input scope differs")
    for row in inputs["sources"]:
        require(row["producer"] == "vendor" and row["disclosed"] is True and digest(Path(row["path"])) == row["sha256"], "disclosed native custody differs")
    output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.part-chronology-process-proof.v1", "passed": False, "source_manifest_sha256": digest(root / "Source01.json"), "base_manifest_sha256": digest(root / "BaselineSource02.json"), "tools_manifest_sha256": digest(root / "Tools03.json"), "input_manifest_sha256": digest(inputs_path), "runner_sha256": digest(Path(__file__)), "workers": [], "sources": [], "builds": [], "rejections": [], "heldout_inputs_read": 0, "native_processes": 0, "full_original_source_preparation_admitted": False}

    def save():
        (output / "Replay.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    def worker(name, tool, arguments, row):
        encoded = json.dumps(row, ensure_ascii=False).encode()
        (output / (name + ".stdin.json")).write_bytes(encoded)
        result = subprocess.run([sys.executable, "-I", "-B", str(root / "Tools03" / tool), "--sdk", str(root / "Code01"), *arguments], input=encoded, capture_output=True, timeout=90)
        (output / (name + ".stdout.json")).write_bytes(result.stdout)
        (output / (name + ".stderr.txt")).write_bytes(result.stderr)
        report["workers"].append({"name": name, "exit_code": result.returncode, "stdin_sha256": sha256(encoded).hexdigest(), "stdout_sha256": sha256(result.stdout).hexdigest(), "stderr_sha256": sha256(result.stderr).hexdigest()})
        save()
        require(result.returncode == 0, "chronology worker failed " + name + " " + result.stderr.decode()[-2400:])
        value = json.loads(result.stdout)
        require(value["passed"] and not value["runtime_external_attempts"] and value["heldout_inputs_read"] == value["native_processes"] == 0, "chronology worker failed its declared boundary")
        for path in value.pop("sdk_modules"):
            require(Path(path).is_relative_to(root / "Code01" / "src"), "SDK import escaped the frozen source")
        return value

    try:
        for index, row in enumerate(inputs["sources"]):
            report["sources"].append(worker("Source" + str(index), "InspectPartChronology04.py", [], row))
            save()
        for index, row in enumerate(inputs["generated_requests"]):
            for mode in ("coupled", "split"):
                report["builds"].append(worker("Build" + str(index) + mode, "AuditChronologyBuild02.py", ["--mode", mode], row))
                save()
        faults = ("duplicate_log_owner", "foreign_feature_owner", "missing_model_event", "modified_first_model_event", "unsupported_owner_class", "owner_schema", "distinct_owner_same_identifier", "boolean_identifier", "unnamed_owner", "duplicate_author_names", "unresolved_author", "unsupported_revision_status", "boolean_event_time", "sentinel_archive_time", "overflow_event_time", "fractional_tick_overflow", "boolean_feature_time", "negative_fraction")
        for index, fault in enumerate(faults):
            report["rejections"].append(worker("Reject" + str(index), "AuditChronologyReject03.py", ["--fault", fault], inputs["generated_requests"][index % 4]))
            save()
        verify(root / "Source01.json", root / "Code01")
        verify(root / "BaselineSource02.json", root / "Baseline01")
        verify(root / "Tools03.json", root / "Tools03")
        require(all(digest(Path(row["path"])) == row["sha256"] for row in inputs["sources"]), "source native inputs changed during proof")
        report["passed"] = True
    except Exception as error:
        report["error"] = repr(error)
    finally:
        report["fresh_processes"] = len(report["workers"])
        report["typed_source_stream_replays"] = 7 * len(report["sources"])
        report["strict_generated_mode_comparisons"] = 2 * len(report["builds"])
        report["positive_nonneutral_filetime_reconstructions"] = sum(sum(value["reconstructed_word_identity"] is True for value in source["feature_instants"]) for source in report["sources"])
        save()
    print(json.dumps({"passed": report["passed"], "processes": report["fresh_processes"], "report_sha256": digest(output / "Replay.json"), "error": report.get("error")}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
