import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def copy_checked(source, target, expected):
    require(
        source.is_file() and not source.is_symlink() and digest(source) == expected,
        "pinned custom-name input changed: " + source.name,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "custom-name frozen destination already exists")
    copyfile(source, target)
    require(digest(target) == expected, "custom-name frozen copy differs")


def prepare(args):
    root = args.parent_packet.resolve(strict=True)
    require(
        digest(root / "Trial.json")
        == "01b767e56dd5f8dd2f1a2c5218a0003b98654f7b9f4eea27369464575172fcd8",
        "parent diagnostic source closure differs",
    )
    parent = json.loads((root / "Trial.json").read_bytes())
    for relative, expected in parent["files_sha256"].items():
        require(digest(root / relative) == expected, "parent diagnostic input changed")
    raw_result = root / "Result.json"
    require(
        digest(raw_result)
        == "e565f5e940076262507fff43296ee1205ccd7fbcfb8eee6ad2ca92d36b6998fa",
        "native parent comparison identity differs",
    )
    native = json.loads(raw_result.read_bytes())
    require(
        native["diagnostic_completed"] is True
        and native["controls_healthy"] is True
        and native["distinct_processes"] == 4
        and native["independent_geometry_and_mate_checks_passed"] is True
        and native["warning_changed_32_to_0"] is True,
        "parent comparison precondition did not pass",
    )
    require(
        all(
            native["phases"][role][stage]["strict_original_capture"]["passed"] is False
            for role in ("ParentOff", "ParentOn")
            for stage in ("before_rebuild", "after_rebuild")
        ),
        "the native authored-name failure must remain explicit",
    )
    require(
        digest(args.api_metadata)
        == "121b887538a8cf22dd5018c73b6be0f5c4c35798fceb28b6a4763374fce95629",
        "registered custom-name metadata differs",
    )
    api = json.loads(args.api_metadata.read_bytes())
    require(
        api["passed"] is True
        and api["enums"]["swExtRefUpdateCompNames"] == 18
        and api["native_processes_started"]
        == api["global_preference_changes"]
        == api["heldout_inputs_read"]
        == 0,
        "registered custom-name metadata is not the zero-CAD preflight",
    )
    require(
        digest(args.intent)
        == "0faaef5ff9bfaf0fb8e2573f758d41ffce6502c4cc93ee3a75006c956a8eb612",
        "independent custom-name intent changed",
    )
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(
        not output.exists() and guest.is_absolute() and guest.name == output.name,
        "choose an unused canonical custom-name packet",
    )
    output.mkdir(parents=True)
    for relative, expected in parent["files_sha256"].items():
        if relative.startswith("Baseline/"):
            copy_checked(root / relative, output / relative, expected)
    for name in ("InspectCustomComponentNames01.py", Path(__file__).name):
        source = Path(__file__).resolve().parent / name
        copy_checked(source, output / "Tools" / name, digest(source))
    copy_checked(
        args.metadata_tool,
        output / "Tools/CaptureComponentNameApi01.py",
        api["tool_sha256"],
    )
    copy_checked(
        args.api_metadata, output / "ApiMetadata.json", digest(args.api_metadata)
    )
    copy_checked(args.intent, output / "Intent.json", digest(args.intent))
    before = {
        "schema": "kit.sw2026.custom-component-name-source-preconditions.v1",
        "parent_ambient_raw_result_sha256": digest(raw_result),
        "parent_ambient_controls_healthy": True,
        "parent_ambient_distinct_processes": 4,
        "parent_ambient_geometry_and_mates_passed": True,
        "parent_ambient_warning_off": [0, 32],
        "parent_ambient_warning_on": [0, 0],
        "parent_authored_name_loss_preserved": True,
        "registered_api_sha256": digest(args.api_metadata),
        "public_name_preference_enum": 18,
        "public_name_preference_must_already_be_false": True,
        "internal_environment_option_0x72_not_equated_to_public_enum": True,
        "native_acceptance": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
    }
    write_json(output / "Preconditions.json", before)
    job = {
        "schema": "kit.sw2026.custom-component-name-control.v1",
        "roles": ["ControlBefore", "Author", "Reopen", "ControlAfter"],
        "scope": "independent native-authored custom occurrence names on ordinary concentric cylinder pair, synchronized save and fresh reopen, no writer output or preference changes",
        "guest_runtime": parent["guest_runtime"],
        "files_sha256": {
            path.relative_to(output).as_posix(): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
        "native_acceptance": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "global_preference_changes": 0,
    }
    write_json(output / "Trial.json", job)
    trial_sha = digest(output / "Trial.json")
    script = str(guest / "Tools/InspectCustomComponentNames01.py")
    trial = str(guest / "Trial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        job["guest_runtime"]["executable"],
        "-B",
        script,
    ]
    tail = [trial, "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.custom-component-name-control-recipe.v1",
        "packet_sha256": trial_sha,
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
            str(output / "Tools/InspectCustomComponentNames01.py"),
            "verify",
            str(output / "Trial.json"),
            "--trial-sha256",
            trial_sha,
        ],
        "guest_verify_argv": [*prefix, "verify", *tail],
        "commands": [
            {
                "role": role,
                "argv": [*prefix, "phase", *tail, "--phase", role],
                "source_control_must_pass_first": role in ("Author", "Reopen"),
                "always_run_after_other_failure": role == "ControlAfter",
            }
            for role in job["roles"]
        ],
        "summary_argv": [*prefix, "summary", *tail],
        "progress_result": str(guest / "Result.json"),
        "source_commit_before_native_required": True,
        "control_after_independent": True,
        "native_processes_started": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "global_preference_changes": 0,
    }
    write_json(output / "Recipe.json", recipe)
    return {
        "packet": str(output),
        "trial_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "frozen_files": len(job["files_sha256"]),
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-packet", type=Path, required=True)
    parser.add_argument("--api-metadata", type=Path, required=True)
    parser.add_argument("--metadata-tool", type=Path, required=True)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
