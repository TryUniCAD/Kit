from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import time

import AuthorEquationSources01 as baseline

BASE = "83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2"
ORIGINAL_ROWS = baseline.equation_rows
SLOTS = ("D01", "Slot01")


def adjacent_rows(case, edited=False):
    rows = ORIGINAL_ROWS(case, edited)
    baseline.require(
        case["family"] == "global_width",
        "the adjacent-unit source cohort admits the global-width family only",
    )
    width = case["edit_width_mm"] if edited else case["width_mm"]
    rows[0] = f'"{case["global_name"]}" = {baseline.number(width)}mm'
    return rows


def verify(path, sha):
    job = baseline.read_job(path, sha)
    scope = job["adjacent_unit_source"]
    baseline.require(
        scope["base_protocol_sha256"] == BASE
        and scope["slots"] == list(SLOTS)
        and scope["changed_input"] == "global assignment numeric/unit adjacency only",
        "the exact adjacent-unit source scope differs",
    )
    return job


def prepare(path, sha, slot):
    job = verify(path, sha)
    baseline.guest_only(job)
    baseline.require(slot in SLOTS, "an undeclared source slot was requested")
    target = baseline.case_root(path, job, slot)
    baseline.require(not target.exists(), "the new source case root must be unused")
    origin = Path(job["adjacent_unit_source"]["original_guest_slot01_root"])
    if slot == "D01" or not origin.exists():
        result = baseline.seal_intents(path, sha, slot)
        result["lineage"] = (
            "unchanged disclosed intent"
            if slot == "D01"
            else "fresh guest-only intent from the predeclared original sampling domain"
        )
        return result
    required = {
        name: origin / name
        for name in ("Intent.json", "Prediction.json", "IntentSeal.json")
    }
    baseline.require(
        all(file.is_file() for file in required.values()),
        "an original private intent is partial; it must not be regenerated",
    )
    old_seal = json.loads(required["IntentSeal.json"].read_bytes())
    baseline.require(
        old_seal["protocol_sha256"] == BASE
        and old_seal["slot"] == slot
        and old_seal["sealed"]
        and old_seal["intent_sha256"] == baseline.digest(required["Intent.json"])
        and old_seal["prediction_sha256"]
        == baseline.digest(required["Prediction.json"]),
        "the independently sealed original intent identity differs",
    )
    case = json.loads(required["Intent.json"].read_bytes())
    baseline.check_case(case, slot)
    prediction = json.loads(required["Prediction.json"].read_bytes())
    baseline.require(
        prediction
        == {
            "Original": baseline.expected(case),
            "Edited": baseline.expected(case, True),
        },
        "the original private prediction disagrees with unchanged source semantics",
    )
    target.mkdir(parents=True)
    for name, source in required.items():
        shutil.copyfile(
            source,
            target / ("OriginalIntentSeal.json" if name == "IntentSeal.json" else name),
        )
    result = {
        "schema": "kit.sw2026.equation-intent-seal.v1",
        "slot": slot,
        "protocol_sha256": sha,
        "intent_sha256": baseline.digest(target / "Intent.json"),
        "prediction_sha256": baseline.digest(target / "Prediction.json"),
        "sealed": True,
        "native_processes_started": 0,
        "writer_output_count": 0,
        "created_at": time.time(),
        "lineage": "byte-identical reuse of the original guest-private sealed intent; no native files or observations read",
        "original_protocol_sha256": BASE,
        "original_intent_seal_sha256": baseline.digest(required["IntentSeal.json"]),
    }
    baseline.write_new(target / "IntentSeal.json", result)
    baseline.publish_progress(path, slot, "IntentSeal", result)
    baseline.require(
        all(
            baseline.digest(required[name])
            == baseline.digest(
                target
                / ("OriginalIntentSeal.json" if name == "IntentSeal.json" else name)
            )
            for name in required
        ),
        "the original private intent changed during isolated reuse",
    )
    return result


def bound_case(path, sha, job, slot):
    baseline.guest_only(job)
    directory, case, seal = baseline.load_case(path, job, slot)
    public = json.loads(
        (path.parent / "Progress" / slot / "IntentSeal" / "Record.json").read_bytes()
    )
    baseline.require(
        seal["protocol_sha256"] == sha
        and seal["slot"] == slot
        and public["protocol_sha256"] == sha
        and public["intent_sha256"] == seal["intent_sha256"]
        and public["prediction_sha256"] == seal["prediction_sha256"]
        and case["family"] == "global_width",
        "the native phase does not match the independently published intent seal",
    )
    return directory, seal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify")
    commands.add_parser("disclosed-plan")
    for name in ("prepare", "lock"):
        commands.add_parser(name).add_argument("--slot", choices=SLOTS, required=True)
    native = commands.add_parser("phase")
    native.add_argument("--slot", choices=SLOTS, required=True)
    native.add_argument("--phase", choices=baseline.PHASES, required=True)
    recovery = commands.add_parser("recover")
    recovery.add_argument("--journal", type=Path, required=True)
    recovery.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    job = verify(args.job, args.sha256)
    if args.command == "verify":
        result = {
            "passed": True,
            "native_processes_started": 0,
            "sealed_inputs_read": 0,
            "files": len(job["files_sha256"]),
            "source_slots": list(SLOTS),
        }
    elif args.command == "disclosed-plan":
        (case,) = [value for value in job["disclosed_cases"] if value["id"] == "D01"]
        result = {
            "passed": True,
            "original_rows": adjacent_rows(case),
            "edited_rows": adjacent_rows(case, True),
            "original_prediction": baseline.expected(case),
            "edited_prediction": baseline.expected(case, True),
            "native_processes_started": 0,
            "sealed_inputs_read": 0,
        }
    elif args.command == "prepare":
        result = prepare(args.job, args.sha256, args.slot)
    elif args.command == "recover":
        result = baseline.recover(args.job, args.sha256, args.journal, args.output)
    else:
        directory, seal = bound_case(args.job, args.sha256, job, args.slot)
        baseline.equation_rows = adjacent_rows
        if args.command == "phase":
            result = baseline.phase(args.job, args.sha256, args.slot, args.phase)
        else:
            for name in baseline.PHASES:
                value = json.loads(
                    (directory / "Inspection" / name / "Result.json").read_bytes()
                )
                baseline.require(
                    value["slot"] == args.slot
                    and value["phase"] == name
                    and value["intent_sha256"] == seal["intent_sha256"]
                    and value["prediction_sha256"] == seal["prediction_sha256"],
                    "the saved native result differs from the fixed intent/prediction",
                )
            result = baseline.lock_case(args.job, args.sha256, args.slot)
    print(json.dumps(result, sort_keys=True))
    return (
        0
        if result.get(
            "passed",
            result.get("source_locked", result.get("native_processes_started") == 0),
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
