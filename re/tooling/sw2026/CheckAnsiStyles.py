from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from ansi_style.JsonDifference import difference


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    root = args.root.resolve(strict=True)
    source = json.loads(args.manifest.read_text())
    for row in source["files"]:
        path = root / row["path"]
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError("frozen source differs: " + row["path"])
    inputs = json.loads(args.requests.read_text())
    observed = json.loads(args.source_observation.read_text())
    if observed["input_sha256"] != inputs["source_intake_sha256"]:
        raise ValueError("source observation belongs to another intake")
    args.output.mkdir(exist_ok=False)
    rows = []
    for ordinal, item in enumerate(inputs["workers"]):
        request = item["request"]
        raw = json.dumps(request, ensure_ascii=False, allow_nan=False).encode()
        prefix = args.output / f"Worker{ordinal:02}"
        prefix.with_suffix(".Request.json").write_bytes(raw)
        command = [
            str(args.python),
            "-B",
            str(root / "re/tooling/sw2026/AnsiStyleProcess.py"),
            str(root),
        ]
        completed = subprocess.run(command, input=raw, capture_output=True, timeout=120)
        prefix.with_suffix(".stdout.json").write_bytes(completed.stdout)
        prefix.with_suffix(".stderr.txt").write_bytes(completed.stderr)
        result = json.loads(completed.stdout)
        passed = (
            (completed.returncode == 0 and result.get("qualified") is True)
            if item["expected"] == "pass"
            else (
                completed.returncode == 1
                and result.get("qualified") is False
                and result.get("error_type") in ("ValueError", "TypeError")
            )
        )
        passed = (
            passed
            and result.get("runtime_input_reads") == 0
            and result.get("runtime_research_imports") == []
        )
        rows.append(
            {
                "ordinal": ordinal,
                "expected": item["expected"],
                "passed": passed,
                "returncode": completed.returncode,
                "request_sha256": hashlib.sha256(raw).hexdigest(),
                "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
                "result": result,
            }
        )
    comparisons = []
    for pair in inputs["comparisons"]:
        iso, ansi = (rows[index]["result"] for index in (pair["iso"], pair["ansi"]))
        if not iso.get("qualified") or not ansi.get("qualified"):
            comparisons.append({**pair, "complete": False})
            continue
        row = {
            **pair,
            "complete": True,
            "iso_to_ansi_typed_diff": difference(iso["fields"], ansi["fields"]),
        }
        if "source_case" in pair:
            case = next(
                item
                for item in observed["styles"]
                if item["case"] == pair["source_case"]
            )
            source_fields = case[pair["source_group"]]
            row["ansi_to_source_typed_diff"] = difference(ansi["fields"], source_fields)
            row["source_fields_faithfully_equal"] = not row["ansi_to_source_typed_diff"]
            row["full_source_admission"] = False
        comparisons.append(row)
    result = {
        "schema": "guarded-ansi-construction-process-v1",
        "source_manifest_sha256": digest(args.manifest),
        "requests_sha256": digest(args.requests),
        "source_observation_sha256": digest(args.source_observation),
        "source_file_count": len(source["files"]),
        "passed": all(row["passed"] for row in rows)
        and all(row["complete"] for row in comparisons),
        "workers": rows,
        "comparisons": comparisons,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "full_original_admission": False,
    }
    for row in source["files"]:
        if digest(root / row["path"]) != row["sha256"]:
            raise ValueError("frozen source changed during the process")
    path = args.output / "Result.json"
    path.write_text(
        json.dumps(
            result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "output": str(path),
                "sha256": digest(path),
                "passed": result["passed"],
                "workers": len(rows),
                "comparisons": len(comparisons),
            }
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--source-observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    raise SystemExit(run(parser.parse_args()))
