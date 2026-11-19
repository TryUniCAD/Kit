from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil

BASE = "83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2"
MATRIX = "c32bc585d8d1e7d329657ec25bd6b24f97fc831b7eba667cdcad328f69ce1cab"
SUMMARY = "d1216d51d75580e1a6fd03acaf214ff25f06642938c8547527e915ec2fd2880c"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def freeze(args):
    if args.output.exists() or digest(args.base / "Protocol.json") != BASE:
        raise ValueError("use the exact source base and an unused adjacent-unit packet")
    measured = args.matrix / "Disclosed/D01/Inspection/Matrix/Result.json"
    if (
        digest(measured) != MATRIX
        or digest(args.matrix / "GlobalSyntaxResult.json") != SUMMARY
    ):
        raise ValueError("the concrete native matrix evidence changed")
    matrix = json.loads(measured.read_bytes())
    summary = json.loads((args.matrix / "GlobalSyntaxResult.json").read_bytes())
    if (
        not matrix["diagnostic_completed"]
        or not summary["controls_healthy"]
        or summary["distinct_processes"] != 3
        or summary["numeric_checks"] != 414
    ):
        raise ValueError(
            "the global syntax matrix is not independently bracketed and complete"
        )
    (row,) = [
        value for value in matrix["cases"] if value["intent"]["id"] == "AdjacentUnit"
    ]
    if (
        not row["publication_observed"]
        or row["add2_return"] != 0
        or row["immediate"]["count"] != 1
        or row["evaluated"]["count"] != 1
        or row["intent"]["text"] != '"source_width" = 31.7mm'
    ):
        raise ValueError(
            "the explicit adjacent-unit global input is not qualified by the matrix"
        )
    job = json.loads((args.base / "Protocol.json").read_bytes())
    prefix = PureWindowsPath(args.guest_packet)
    private = PureWindowsPath(args.guest_private_root)
    if (
        not prefix.is_absolute()
        or not str(prefix).startswith(
            "\\\\Mac\\Home\\Documents\\UniCAD\\Oracle121Takeover\\"
        )
        or not private.is_absolute()
        or private.drive.casefold() != "c:"
        or len(private.parts) != 2
        or str(private).casefold() == job["guest_private_root"].casefold()
    ):
        raise ValueError(
            "use explicit mounted packet and distinct guest-private output identities"
        )
    args.output.mkdir(parents=True)
    for relative, sha in job["files_sha256"].items():
        source = args.base / relative
        if digest(source) != sha:
            raise ValueError("the original frozen source dependency changed")
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for name in (
        "AuthorAdjacentEquationSources01.py",
        "FreezeAdjacentEquationSources01.py",
    ):
        source = Path(__file__).resolve().parent / name
        target = args.output / "Tools" / name
        shutil.copyfile(source, target)
        job["files_sha256"]["Tools/" + name] = digest(target)
    receipt = {
        "schema": "kit.sw2026.global-unit-adjacency-native-finding.v1",
        "matrix_result_sha256": MATRIX,
        "summary_sha256": SUMMARY,
        "diagnostic_completed": True,
        "controls_healthy": True,
        "distinct_native_processes": 3,
        "numeric_checks": 414,
        "members": [
            {
                "id": value["intent"]["id"],
                "input": value["intent"],
                "return": value["add2_return"],
                "status_after_add2": value["status_immediately_after_add2"],
                "immediate_count": value["immediate"]["count"],
                "evaluated_count": value["evaluated"]["count"],
                "publication_observed": value["publication_observed"],
                "raw_rows": value["evaluated"]["rows"],
            }
            for value in matrix["cases"]
        ],
        "phase_sha256": summary["result_sha256"],
        "writer_output_count": 0,
        "native_files_saved": 0,
        "source_lock_produced": False,
        "native_writer_qualified": False,
    }
    publish(args.output / "MatrixFinding01.json", receipt)
    job["files_sha256"]["MatrixFinding01.json"] = digest(
        args.output / "MatrixFinding01.json"
    )
    old_private = PureWindowsPath(job["guest_private_root"]) / "Slot01"
    job["guest_private_root"] = str(private)
    job["adjacent_unit_source"] = {
        "base_protocol_sha256": BASE,
        "slots": ["D01", "Slot01"],
        "changed_input": "global assignment numeric/unit adjacency only",
        "matrix_result_sha256": MATRIX,
        "original_guest_slot01_root": str(old_private),
        "original_intent_policy": "reuse exact original intent/prediction if present; otherwise guest-seal from the unchanged preregistered sampler; never overwrite original private data",
        "native_source_before_writer_required": True,
    }
    publish(args.output / "Protocol.json", job)
    sha = digest(args.output / "Protocol.json")
    command = [
        job["guest_runtime"]["executable"],
        "-B",
        str(prefix / "Tools/AuthorAdjacentEquationSources01.py"),
        "--job",
        str(prefix / "Protocol.json"),
        "--sha256",
        sha,
    ]
    phases = []
    for slot in ("D01", "Slot01"):
        phases.append(
            {
                "slot": slot,
                "prepare_argv": command + ["prepare", "--slot", slot],
                "phases": [
                    {
                        "phase": role,
                        "argv": command + ["phase", "--slot", slot, "--phase", role],
                        "requires_author_success": role.startswith("Reopen"),
                        "run_even_on_prior_failure": role == "ControlAfter",
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
                "lock_argv": command + ["lock", "--slot", slot],
            }
        )
    publish(
        args.output / "Recipe01.json",
        {
            "schema": "kit.sw2026.adjacent-global-source-recipe.v1",
            "protocol_sha256": sha,
            "verify_argv": command + ["verify"],
            "stages": phases,
            "recovery_argv_prefix": command + ["recover"],
            "recovery_arguments": [
                "--journal",
                "EXACT_OWNED_AUTHOR_PREFERENCE_JOURNAL",
                "--output",
                "UNUSED_GUEST_RECOVERY_RECEIPT",
            ],
            "only_root_executes_native": True,
            "native_processes_planned": 10,
            "sealed_intents_read_or_created_during_freeze": 0,
            "writer_output_count": 0,
        },
    )
    publish(
        args.output / "PacketManifest01.json",
        {
            "schema": "kit.sw2026.adjacent-global-source-packet.v1",
            "files_sha256": {
                str(path.relative_to(args.output)).replace("\\", "/"): digest(path)
                for path in sorted(args.output.rglob("*"))
                if path.is_file()
            },
        },
    )
    return {
        "passed": True,
        "protocol_sha256": sha,
        "recipe_sha256": digest(args.output / "Recipe01.json"),
        "manifest_sha256": digest(args.output / "PacketManifest01.json"),
        "native_processes_started": 0,
        "sealed_inputs_read_or_created": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    parser.add_argument("--guest-private-root", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
