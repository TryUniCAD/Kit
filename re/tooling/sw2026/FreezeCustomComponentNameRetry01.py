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
        "retry input changed: " + source.name,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "retry frozen destination already exists")
    copyfile(source, target)
    require(digest(target) == expected, "retry frozen copy differs")


def prepare(args):
    prior = args.prior_packet.resolve(strict=True)
    require(
        digest(prior / "Trial.json")
        == "7c2dc5ed8f9490237620ac212e74c003f36d4ca2cedbe754563fe1d0b3d14b2b",
        "original custom-name packet differs",
    )
    old = json.loads((prior / "Trial.json").read_bytes())
    for relative, expected in old["files_sha256"].items():
        require(
            digest(prior / relative) == expected, "original custom-name input changed"
        )
    require(
        digest(prior / "Result.json")
        == "03b6fc14e48364f0ada77bf9c13c3e1b3d8f84a36a5bf7e577117db21508aa1c",
        "prior true-preference native result differs",
    )
    failed = json.loads((prior / "Result.json").read_bytes())
    require(
        failed["passed"] is False
        and failed["controls_healthy"] is True
        and failed["distinct_processes"] == 3
        and failed["phases"]["Author"]["name_update_preference"] is True
        and failed["phases"]["Author"]["name_update_preference_after"] is True,
        "preserve the controlled pre-source prerequisite failure",
    )
    require(
        digest(args.api_metadata) == args.api_sha256, "actual setter metadata changed"
    )
    api = json.loads(args.api_metadata.read_bytes())
    require(
        api["schema"] == "kit.sw2026.component-name-setter-api-metadata.v1"
        and api["passed"] is True
        and api["enums"]["swExtRefUpdateCompNames"] == 18
        and api["native_processes_started"] == api["global_preference_changes"] == 0,
        "registered setter prerequisite differs",
    )
    setter = [
        row
        for row in api["interfaces"]["ISldWorks"]["members"]
        if row["names"][0] == "SetUserPreferenceToggle"
    ]
    require(
        len(setter) == 1
        and setter[0]["invoke_kind"] == 1
        and setter[0]["arguments"] == "((3, 1, None), (11, 1, None))",
        "setter requires the actual registered integer/Boolean call shape",
    )
    original_api = json.loads((prior / "ApiMetadata.json").read_bytes())
    require(
        api["base_tool_sha256"] == original_api["tool_sha256"],
        "registered base metadata collector changed",
    )
    for interface, value in original_api["interfaces"].items():
        require(
            value["guid"] == api["interfaces"][interface]["guid"]
            and all(
                row in api["interfaces"][interface]["members"]
                for row in value["members"]
            ),
            "registered prior interfaces changed",
        )
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(
        not output.exists() and guest.is_absolute() and guest.name == output.name,
        "choose an unused retry packet",
    )
    output.mkdir(parents=True)
    for relative, expected in old["files_sha256"].items():
        if relative != "ApiMetadata.json":
            copy_checked(prior / relative, output / relative, expected)
    copy_checked(
        prior / "ApiMetadata.json",
        output / "ApiMetadataOriginal.json",
        digest(prior / "ApiMetadata.json"),
    )
    copy_checked(args.api_metadata, output / "ApiMetadata.json", args.api_sha256)
    for name in (
        "CaptureComponentNameSetterApi01.py",
        "ComponentNamePreferenceLease.py",
        "InspectCustomComponentNameRetry01.py",
        Path(__file__).name,
    ):
        source = Path(__file__).resolve().parent / name
        if name == "CaptureComponentNameSetterApi01.py":
            require(
                digest(source) == api["tool_sha256"],
                "setter metadata collector source differs",
            )
        copy_checked(source, output / "Tools" / name, digest(source))
    authorization = {
        "schema": "kit.sw2026.custom-component-name-owned-preference-authorization.v1",
        "scope": "temporary SetUserPreferenceToggle(18,False) in the owned source author/save session only, capture before mutation, durable journal, finally restore and verify actual original value",
        "preference_enum": 18,
        "temporary_value": False,
        "supersedes_only": "original intent preference_policy.changes_authorized",
        "fresh_reopen": "primary under the actual original setting with no mutation",
        "recovery": "fresh owned oracle only after confirming no surviving or foreign CAD process; restore only the durable captured original value",
        "other_preferences_may_change": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
    }
    write_json(output / "PreferenceAuthorization.json", authorization)
    write_json(
        output / "PriorFailure.json",
        {
            "schema": "kit.sw2026.custom-component-name-prerequisite-failure.v1",
            "raw_result_sha256": digest(prior / "Result.json"),
            "controls_healthy": True,
            "distinct_processes": 3,
            "original_preference": True,
            "preference_unchanged": True,
            "source_created": False,
            "writer_outputs": 0,
        },
    )
    job = {
        "schema": "kit.sw2026.custom-component-name-preference-retry.v1",
        "roles": ["ControlBefore", "Author", "Reopen", "ControlAfter"],
        "guest_runtime": old["guest_runtime"],
        "superseded_intent_field": "preference_policy.changes_authorized",
        "temporary_preference_enum": 18,
        "temporary_preference_change_authorized": True,
        "reopen_under_captured_original_setting": True,
        "files_sha256": {
            path.relative_to(output).as_posix(): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
        "native_acceptance": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
    }
    write_json(output / "Trial.json", job)
    trial_sha = digest(output / "Trial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        job["guest_runtime"]["executable"],
        "-B",
        str(guest / "Tools/InspectCustomComponentNameRetry01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.custom-component-name-preference-retry-recipe.v1",
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
            str(output / "Tools/InspectCustomComponentNameRetry01.py"),
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
        "recovery_argv": [
            *prefix,
            "recover",
            *tail,
            "--recovery-output",
            str(guest / "Recovery01"),
        ],
        "recovery_condition": "author process died or preference restoration failed; durable Captured.json required; old owned process must be gone and oracle idle",
        "progress_result": str(guest / "Result.json"),
        "durable_preference_directory": str(guest / "Inspection/Author/Preference"),
        "source_commit_before_native_required": True,
        "control_after_independent": True,
        "native_processes_started": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
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
    parser.add_argument("--prior-packet", type=Path, required=True)
    parser.add_argument("--api-metadata", type=Path, required=True)
    parser.add_argument("--api-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
