import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.diagnostic.resolve(strict=True)
    if (
        digest(source)
        != "c0fd9c34be82a7b506b49d90a1a41688228e57175defb3ff6a805af5e6d1a363"
    ):
        raise ValueError(
            "expected the exact unchanged original generated-pair diagnostic"
        )
    files = source.parent / "DiagnosticFiles.json"
    if (
        digest(files)
        != "bee4a972e540934ccca713d5465f1199aba862066a17f61a47630fa7a8601600"
    ):
        raise ValueError("original diagnostic source closure changed")
    entries = json.loads(files.read_bytes())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for relative, row in entries.items():
        path = source.parent / relative
        if digest(path) != row["sha256"]:
            raise ValueError("original frozen diagnostic file changed: " + relative)
        if relative in ("DiagnosticTrial.json", "Recipe.json"):
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(path, target)
    for name in ("InspectConcentricNames01.py", "PrepareConcentricNames01.py"):
        copyfile(Path(__file__).with_name(name), output / "DiagnosticTools" / name)
    config = json.loads(source.read_bytes())
    config.update(
        name_probe_schema="kit.sw2026.concentric-reference-name-probe.v1",
        roles=["ControlBefore", "ParentRebuild", "ControlAfter"],
        scope="exact original generated parent; actual reference IFeature.Name and IComponent2.Name2 before the unchanged strict name gate; no preference or source edits",
    )
    config["name_files_sha256"] = {
        str(path.relative_to(output)): digest(path)
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    trial = output / "DiagnosticTrial.json"
    write_json(trial, config)
    trial_hash = digest(trial)
    if not output.is_relative_to(Path("/Users/odin/Documents")):
        raise ValueError(
            "the frozen mounted source requires the declared host Documents locator"
        )
    guest = PureWindowsPath(r"\\Mac\Home\Documents") / str(
        output.relative_to(Path("/Users/odin/Documents"))
    ).replace("/", "\\")
    base_job = json.loads((output / "Trial.json").read_bytes())
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        base_job["guest_runtime"]["executable"],
        "-B",
        str(guest / "DiagnosticTools/InspectConcentricNames01.py"),
    ]
    roles = config["roles"]
    recipe = {
        "schema": "kit.sw2026.concentric-reference-name-recipe.v1",
        "packet_sha256": trial_hash,
        "commands": [
            {
                "role": role,
                "argv": prefix
                + [
                    "phase",
                    str(guest / trial.name),
                    "--sha256",
                    trial_hash,
                    "--role",
                    role,
                ],
                "always_run_after_other_failure": role == "ControlAfter",
                "source_control_must_pass_first": role == "ParentRebuild",
            }
            for role in roles
        ],
        "guest_verify_argv": prefix
        + ["verify", str(guest / trial.name), "--sha256", trial_hash],
        "host_verify_argv": [
            "uv",
            "run",
            "--no-project",
            "--offline",
            "--isolated",
            "--python",
            "3.11",
            "python",
            "-B",
            str(output / "DiagnosticTools/InspectConcentricNames01.py"),
            "verify",
            str(trial),
            "--sha256",
            trial_hash,
        ],
        "summary_argv": prefix
        + ["summary", str(guest / trial.name), "--sha256", trial_hash],
        "progress_result": str(guest / "NameResult.json"),
        "control_after_independent": True,
        "native_processes_started": 0,
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "global_preference_changes": 0,
        "source_commit_before_native_required": True,
    }
    write_json(output / "Recipe.json", recipe)
    print(
        json.dumps(
            {
                "trial_sha256": trial_hash,
                "recipe_sha256": digest(output / "Recipe.json"),
                "files": len(config["name_files_sha256"]),
                "native_acceptance": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
