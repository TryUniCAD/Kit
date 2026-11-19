from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil

BASE_SHA = "83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2"
FAILED_SHA = "a6d6ed7149988f6cc7861e3a97b281adc200667bce413386f5c68b0b7394fab3"
RECORD_SHA = "84db9a5778000562e6a7e62b752459fead0863e57d18c8958f060b5aa0f6a5e9"
BRACKETS = {
    "ControlBefore": "4177240ecc52b414e1b72c637f71394ff9412e5cd616ee8c78ea65f9d6c68145",
    "ControlAfter": "1fc223a506258d1709a6c80de9399ddb5092bb2f49c30531afd950a79e44a0a4",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def freeze(args):
    if args.output.exists() or digest(args.base / "Protocol.json") != BASE_SHA:
        raise ValueError("use the exact frozen base and an unused successor root")
    job = json.loads((args.base / "Protocol.json").read_bytes())
    inspection = args.base / "Disclosed/D01/Inspection"
    if (
        digest(inspection / "Author/Result.json") != FAILED_SHA
        or digest(inspection / "Author/Record.json") != RECORD_SHA
    ):
        raise ValueError("the exact disclosed Add2 failure changed")
    failed = json.loads((inspection / "Author/Result.json").read_bytes())
    if failed["passed"] or failed["files"]:
        raise ValueError(
            "the original first failure must remain a failed source phase without native saves"
        )
    raw = json.loads((inspection / "Author/Record.json").read_bytes())
    calls = [
        value for value in raw["api_calls"] if value["method"] == "IEquationMgr.Add2"
    ]
    if (
        len(calls) != 1
        or calls[0]["arguments"]["values"] != [0, '"source_width" = 31.7 mm', False]
        or calls[0]["result"] != -1
    ):
        raise ValueError("the original Add2 call identity differs")
    controls = {}
    for role, expected in BRACKETS.items():
        path = inspection / role / "Result.json"
        value = json.loads(path.read_bytes())
        if (
            digest(path) != expected
            or not value["passed"]
            or value["open_status"] != [0, 0]
        ):
            raise ValueError("the original pristine control did not qualify")
        controls[role] = {
            "sha256": expected,
            "oracle_identity": value["oracle_identity"],
            "numeric_checks": value["numeric_checks"],
        }
    preference = json.loads((inspection / "Author/PreferenceLease.json").read_bytes())
    if (
        not preference["restored"]
        or preference["restore_required"]
        or preference["original"] is not False
    ):
        raise ValueError("the measured actual preference restoration differs")
    prefix = PureWindowsPath(args.guest_packet)
    if not prefix.is_absolute() or not str(prefix).startswith(
        "\\\\Mac\\Home\\Documents\\UniCAD\\Oracle121Takeover\\"
    ):
        raise ValueError("the successor needs its exact mounted guest identity")
    args.output.mkdir(parents=True)
    for name, expected in job["files_sha256"].items():
        current = args.base / name
        if digest(current) != expected:
            raise ValueError("a frozen base dependency changed")
        target = args.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(current, target)
    for name in (
        "InspectEquationAdd2Publication01.py",
        "FreezeEquationPublication01.py",
    ):
        current = Path(__file__).resolve().parent / name
        target = args.output / "Tools" / name
        shutil.copyfile(current, target)
        job["files_sha256"]["Tools/" + name] = digest(target)
    failure = {
        "schema": "kit.sw2026.equation-add2-first-failure.v1",
        "base_protocol_sha256": BASE_SHA,
        "author_result_sha256": FAILED_SHA,
        "author_record_sha256": RECORD_SHA,
        "first_call": calls[0],
        "controls": controls,
        "author_oracle_identity": failed["oracle_identity"],
        "preference_original": False,
        "preference_restored": True,
        "native_source_files_saved": 0,
        "writer_output_count": 0,
        "sealed_inputs_read": 0,
        "publication_after_call_measured": False,
        "original_failure_retained": True,
    }
    publish(args.output / "FirstFailure.json", failure)
    job["files_sha256"]["FirstFailure.json"] = digest(args.output / "FirstFailure.json")
    job["publication_probe"] = {
        "base_protocol_sha256": BASE_SHA,
        "only_disclosed_slot": "D01",
        "input_change_count": 0,
        "changed_observer": "capture actual post-Add2 publication before grading; EvaluateAll between additions",
        "cohort_or_hidden_authoring_authorized_by_this_probe": False,
    }
    publish(args.output / "Protocol.json", job)
    wanted = digest(args.output / "Protocol.json")
    command = [
        job["guest_runtime"]["executable"],
        "-B",
        str(prefix / "Tools/InspectEquationAdd2Publication01.py"),
        "--job",
        str(prefix / "Protocol.json"),
        "--sha256",
        wanted,
    ]
    recipe = {
        "schema": "kit.sw2026.equation-add2-publication-recipe.v1",
        "protocol_sha256": wanted,
        "base_protocol_sha256": BASE_SHA,
        "verify_argv": command + ["verify"],
        "seal_argv": command + ["seal"],
        "phases": [
            {
                "phase": role,
                "argv": command + ["phase", "--phase", role],
                "requires_prior_author_success": role.startswith("Reopen"),
                "run_even_if_author_failed": role == "ControlAfter",
                "recommended_transport_timeout_seconds": 360,
            }
            for role in (
                "ControlBefore",
                "Author",
                "ReopenOriginal",
                "ReopenEdited",
                "ControlAfter",
            )
        ],
        "lock_argv": command + ["lock"],
        "recovery_argv_prefix": command + ["recover"],
        "sealed_slots_included_in_execution": False,
        "native_processes_executed_during_freeze": 0,
        "writer_output_count": 0,
    }
    publish(args.output / "Recipe01.json", recipe)
    publish(
        args.output / "PacketManifest01.json",
        {
            "schema": "kit.sw2026.equation-add2-publication-packet.v1",
            "files_sha256": {
                str(path.relative_to(args.output)).replace("\\", "/"): digest(path)
                for path in sorted(args.output.rglob("*"))
                if path.is_file()
            },
        },
    )
    return {
        "passed": True,
        "protocol_sha256": wanted,
        "recipe_sha256": digest(args.output / "Recipe01.json"),
        "manifest_sha256": digest(args.output / "PacketManifest01.json"),
        "native_processes_started": 0,
        "sealed_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
