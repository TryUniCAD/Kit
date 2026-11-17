from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath

from PrepareDimensionedAssemblyPredictions import CONTROL, SOURCE_LOCK, checked_json, digest, json_bytes, write


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def check_predictions(stage, expected_hash, lock):
    predicted = checked_json(stage / "Predictions.json", expected_hash)
    if predicted["source_lock_sha256"] != SOURCE_LOCK or predicted["specs_sha256"] != lock["specs_sha256"]:
        raise ValueError("predictions do not identify the preregistered source cases")
    cases = {row["name"]: row for row in lock["cases"] if row["split"] == "heldout"}
    if predicted["split"] != "heldout" or [row["name"] for row in predicted["cases"]] != list(cases):
        raise ValueError("prediction cohort differs from the sealed lock")
    for row in predicted["cases"]:
        for trial in row["trials"]:
            folder = stage / "Generated" / row["name"] / trial["title"]
            for name, expected in trial["files"].items():
                if digest((folder / name).read_bytes()) != expected:
                    raise ValueError("generated native file differs from its frozen prediction")
            for label, name in (("writer_request_sha256", "WriterRequest.json"), ("archive_checks_sha256", "ArchiveChecks.json")):
                checked_json(folder / name, trial[label])
    return predicted, cases


def bind_native(case, source_root, stage):
    name = case["name"]
    root = source_root / name
    author, reopened = (
        checked_json(root / folder / "Record.json", fingerprint)
        for folder, fingerprint in zip(("author", "fresh-reopen"), case["record_sha256"], strict=True)
    )
    for record in (author, reopened):
        state = record["assembly_result"]
        if not record["passed"] or not state["passed"] or state["oracle_identity"]["sha256"] != ORACLE:
            raise ValueError(f"locked native reference is unqualified: {name}")
    rebuilt = reopened["assembly_result"]["rebuilt"]
    tree = rebuilt["tree"]
    if not tree or any(node["error"] != 0 or node["warning"] for node in tree):
        raise ValueError(f"locked reference tree has native diagnostics: {name}")
    child_record = case["synchronized_child"]
    if child_record["path_basename"] != "CohortChild.SLDPRT":
        raise ValueError("locked child identity differs from the neutral reference")
    artifacts = {name + ".SLDASM": case["native_sha256"], "CohortChild.SLDPRT": child_record["native_sha256"]}
    destination = stage / "NativeSources" / name
    destination.mkdir(parents=True, exist_ok=False)
    for filename, expected in artifacts.items():
        data = (root / "author" / filename).read_bytes()
        if digest(data) != expected:
            raise ValueError(f"locked native reference bytes differ: {filename}")
        write(destination / filename, data)
    return {
        "files": artifacts, "verified_record_sha256": case["record_sha256"],
        "native_root_tree": {"ordered_nodes": [{key: node[key] for key in ("name", "type", "parent")} for node in tree]},
    }


def main():
    parser = argparse.ArgumentParser(description="Bind independently locked native assembly references after prediction freeze")
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--predictions-sha256", required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--guest-root", type=PureWindowsPath, required=True)
    parser.add_argument("--guest-checkout", type=PureWindowsPath, required=True)
    args = parser.parse_args()
    lock = checked_json(args.source_lock, SOURCE_LOCK)
    predicted, cases = check_predictions(args.stage, args.predictions_sha256, lock)
    if not args.guest_root.is_absolute() or not args.guest_checkout.is_absolute():
        raise ValueError("guest staging and checkout paths must be absolute")
    control = args.control.read_bytes()
    if digest(control) != CONTROL or lock["control_sha256"] != CONTROL:
        raise ValueError("native control differs from the frozen source")
    snapshot = {
        "source_revision": lock["source_revision"],
        "source_lock_sha256": SOURCE_LOCK, "predictions_sha256": args.predictions_sha256,
        "cases": {name: bind_native(case, args.source_root, args.stage) for name, case in cases.items()},
    }
    control_file = Path("Control") / "L1_boss.SLDPRT"
    (args.stage / control_file.parent).mkdir(exist_ok=False)
    write(args.stage / control_file, control)
    snapshot_hash = write(args.stage / "SourceSnapshot.json", json_bytes(snapshot))
    job_hash = write(args.stage / "Job.json", json_bytes({
        "schema": "kit.sw2026.dimensioned-assembly-heldout-job.v1", "stage": str(args.guest_root),
        "output": str(args.guest_root / "Inspection"), "checkout_root": str(args.guest_checkout),
        "source_snapshot_sha256": snapshot_hash, "predictions_sha256": args.predictions_sha256,
        "oracle_sha256": ORACLE, "control": {"file": str(control_file), "sha256": CONTROL},
        "generator": {"commit": predicted["generator_revision"], "tree": predicted["generator_tree"], "adapter": "research_assembly_bundle"},
        "cases": predicted["cases"], "dimensions": predicted["dimensions"], "geometry": predicted["geometry"],
    }))
    print(json.dumps({"job_sha256": job_hash, "source_snapshot_sha256": snapshot_hash, "cases": len(cases)}))


if __name__ == "__main__":
    main()
