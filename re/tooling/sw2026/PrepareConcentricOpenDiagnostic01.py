from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil

BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"
FAILURE = "8a58723e84e741b2788b9c1c8618f1947bb22361b36c6e8309a2aa21fb1d34cf"
ROLES = ("ControlBefore", "StandaloneChild", "ParentRebuild", "ControlAfter")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(
            json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )


def prepare(args):
    base = args.source_packet.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "use an unused diagnostic packet")
    require(
        digest(base / "Trial.json") == BASE_TRIAL and digest(args.failure) == FAILURE,
        "exact failed native job or receipt differs",
    )
    job = json.loads((base / "Trial.json").read_bytes())
    negative = json.loads(args.failure.read_bytes())
    require(
        negative["controls_healthy"]
        and negative["distinct_native_processes"] == 6
        and negative["generated_native_passes"] == 0,
        "retain the measured failed outcomes and healthy controls",
    )
    files = {"Trial.json": BASE_TRIAL, "OriginalProtocol.json": job["protocol_sha256"]}
    for name, expected in job["tools_sha256"].items():
        files["Tools/" + name] = expected
        compile(ast.parse((base / "Tools" / name).read_bytes()), name, "exec")
    for case in job["cases"].values():
        for item in case["inputs"].values():
            require(
                digest(Path(item["host_path"])) == item["sha256"],
                "original native input changed",
            )
        for item in case["evidence"].values():
            files[item["path"]] = item["sha256"]
        files[case["prediction_path"]] = case["prediction_sha256"]
    runtime = job["guest_runtime"]
    files[runtime["receipt_path"]] = runtime["receipt_sha256"]
    for name, expected in files.items():
        source = (base / name).resolve(strict=True)
        require(
            source.is_relative_to(base) and digest(source) == expected,
            "frozen observer file differs: " + name,
        )
    inspector = Path(__file__).with_name("InspectConcentricOpenDiagnostic01.py")
    compile(ast.parse(inspector.read_bytes()), str(inspector), "exec")
    guest = PureWindowsPath(args.guest_packet)
    python = PureWindowsPath(runtime["executable"])
    require(
        guest.is_absolute() and python.is_absolute(),
        "guest packet and interpreter must be absolute",
    )
    output.mkdir()
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / name, target)
    shutil.copyfile(args.failure, output / "NativeFailure.json")
    tools = output / "DiagnosticTools"
    tools.mkdir()
    shutil.copyfile(inspector, tools / inspector.name)
    config = {
        "schema": "kit.sw2026.concentric-open-diagnostic.v1",
        "base_trial_sha256": BASE_TRIAL,
        "case": "Feature",
        "native_failure_sha256": FAILURE,
        "inspector_sha256": digest(inspector),
        "freezer_sha256": digest(Path(__file__)),
        "roles": list(ROLES),
        "scope": "read-only standalone-child and parent rebuild-state diagnostics between strict original controls",
        "file_saves": 0,
        "parameter_edits": 0,
        "warning32_is_not_acceptance": True,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
    }
    trial = output / "DiagnosticTrial.json"
    write_json(trial, config)
    wanted = digest(trial)
    script = str(guest / "DiagnosticTools" / inspector.name)
    target = str(guest / "DiagnosticTrial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        str(python),
        "-B",
        script,
    ]
    recipe = {
        "schema": "kit.sw2026.concentric-open-diagnostic-recipe.v1",
        "packet_sha256": wanted,
        "verify_argv": prefix + ["verify", target, "--sha256", wanted],
        "commands": [
            {
                "role": role,
                "argv": prefix + ["phase", target, "--sha256", wanted, "--role", role],
                "always_run_after_other_failure": role == "ControlAfter",
                "source_control_must_pass_first": role
                in ("StandaloneChild", "ParentRebuild"),
            }
            for role in ROLES
        ],
        "summary_argv": prefix + ["summary", target, "--sha256", wanted],
        "progress_result": str(guest / "DiagnosticResult.json"),
        "control_after_independent": True,
        "source_commit_before_native_required": True,
        "native_processes_started": 0,
        "native_acceptance": False,
    }
    write_json(output / "Recipe.json", recipe)
    frozen = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    write_json(output / "DiagnosticFiles.json", frozen)
    return {
        "trial_sha256": wanted,
        "recipe_sha256": digest(output / "Recipe.json"),
        "files_sha256": digest(output / "DiagnosticFiles.json"),
        "copied_baseline_files": len(files),
        "native_processes_started": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("source-packet", "failure", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
