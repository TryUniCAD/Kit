from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil

BASE = "83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2"
AUTHOR = "ac2043420ba18d5d9258fdd42bf4020b7657505d279924207b3283b35d634f31"
RECORD = "cb327e1cb140faa993f404b5463db43389f2ce75b30020b0052c118842a321bf"
CONTROLS = {
    "ControlBefore": "8f4824cb498c6447ce7c4753c033dbb9c5fdde89850979b5acb1ac15274299c6",
    "ControlAfter": "6d6410036379d36168f9c8b9eaee54d0746bf13c0aee9f9f86bb1e14093f9ea4",
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
    if args.output.exists() or digest(args.base / "Protocol.json") != BASE:
        raise ValueError(
            "use the unchanged source protocol and an unused matrix output"
        )
    observed = args.publication / "Disclosed/D01/Inspection"
    if (
        digest(observed / "Author/Result.json") != AUTHOR
        or digest(observed / "Author/Record.json") != RECORD
    ):
        raise ValueError("the measured same-input publication failure changed")
    raw = json.loads((observed / "Author/Record.json").read_bytes())
    probe = raw["add2_publication_probe"]
    (call,) = probe["calls"]
    if (
        call["add2_return"] != -1
        or call["status_immediately_after_add2"] != -1
        or call["immediate_publication"]["count"] != 0
        or call["evaluated_publication"]["count"] != 0
    ):
        raise ValueError("the measured publication frontier differs")
    controls = {}
    for role, sha in CONTROLS.items():
        path = observed / role / "Result.json"
        value = json.loads(path.read_bytes())
        if digest(path) != sha or not value["passed"] or value["open_status"] != [0, 0]:
            raise ValueError(
                "the publication failure is not bracketed by healthy controls"
            )
        controls[role] = {
            "result_sha256": sha,
            "oracle_identity": value["oracle_identity"],
            "numeric_checks": value["numeric_checks"],
        }
    job = json.loads((args.base / "Protocol.json").read_bytes())
    prefix = PureWindowsPath(args.guest_packet)
    if not prefix.is_absolute() or not str(prefix).startswith(
        "\\\\Mac\\Home\\Documents\\UniCAD\\Oracle121Takeover\\"
    ):
        raise ValueError("the matrix needs an explicit mounted guest identity")
    args.output.mkdir(parents=True)
    for relative, sha in job["files_sha256"].items():
        current = args.base / relative
        if digest(current) != sha:
            raise ValueError("the frozen baseline source dependency changed")
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(current, target)
    for name in ("InspectEquationGlobalSyntax01.py", "FreezeEquationGlobalSyntax01.py"):
        source = Path(__file__).resolve().parent / name
        target = args.output / "Tools" / name
        shutil.copyfile(source, target)
        job["files_sha256"]["Tools/" + name] = digest(target)
    tree = ast.parse(
        (args.output / "Tools/InspectEquationGlobalSyntax01.py").read_text()
    )
    (cases,) = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "CASES"
            for target in node.targets
        )
    ]
    failure = {
        "schema": "kit.sw2026.equation-global-publication-failure.v1",
        "original_source_protocol_sha256": BASE,
        "same_input_author_result_sha256": AUTHOR,
        "same_input_record_sha256": RECORD,
        "native_call": call,
        "controls": controls,
        "actual_publication_failed": True,
        "native_source_saved": False,
        "sealed_inputs_read": 0,
        "writer_output_count": 0,
    }
    publish(args.output / "PublicationFailure01.json", failure)
    job["files_sha256"]["PublicationFailure01.json"] = digest(
        args.output / "PublicationFailure01.json"
    )
    job["global_syntax_matrix"] = {
        "cases": list(cases),
        "source_case": "D01",
        "new_part_per_member": True,
        "matrix_native_applications": 1,
        "pristine_control_applications": 2,
        "writer_output_count": 0,
        "document_saves": 0,
        "sealed_inputs_read": 0,
        "native_acceptance": False,
        "global_values_unit_domain": "recorded raw; not guessed",
        "profile_geometry": "exact original D01 corner rectangle and blind boss",
        "preference_journal": "Disclosed/D01/Inspection/Author/PreferenceLease.json",
        "recovery_policy": "the unchanged source-author recover command restores the actual captured prompt value",
    }
    publish(args.output / "Protocol.json", job)
    sha = digest(args.output / "Protocol.json")
    command = [
        job["guest_runtime"]["executable"],
        "-B",
        str(prefix / "Tools/InspectEquationGlobalSyntax01.py"),
        "--job",
        str(prefix / "Protocol.json"),
        "--sha256",
        sha,
    ]
    recovery = [
        job["guest_runtime"]["executable"],
        "-B",
        str(prefix / "Tools/AuthorEquationSources01.py"),
        "--job",
        str(prefix / "Protocol.json"),
        "--sha256",
        sha,
        "recover",
        "--journal",
        str(prefix / "Disclosed/D01/Inspection/Author/PreferenceLease.json"),
        "--output",
        str(prefix / "MatrixRecovery01.json"),
    ]
    recipe = {
        "schema": "kit.sw2026.equation-global-syntax-recipe.v1",
        "protocol_sha256": sha,
        "verify_argv": command + ["verify"],
        "seal_argv": command + ["seal"],
        "phases": [
            {
                "phase": name,
                "argv": command + [name],
                "recommended_transport_timeout_seconds": (
                    900 if name == "Matrix" else 360
                ),
                "run_after_previous_failure": name == "ControlAfter",
            }
            for name in ("ControlBefore", "Matrix", "ControlAfter")
        ],
        "summary_argv": command + ["summary"],
        "recovery_argv": recovery,
        "native_acceptance": False,
        "native_source_locks_produced": 0,
        "sealed_execution_included": False,
    }
    publish(args.output / "Recipe01.json", recipe)
    publish(
        args.output / "PacketManifest01.json",
        {
            "schema": "kit.sw2026.equation-global-syntax-packet.v1",
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
        "matrix_members": len(cases),
        "native_processes_started": 0,
        "sealed_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--publication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
