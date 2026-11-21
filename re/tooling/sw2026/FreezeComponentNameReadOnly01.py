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
        "read-only source changed: " + source.name,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "read-only frozen destination already exists")
    copyfile(source, target)
    require(digest(target) == expected, "read-only frozen copy differs")


def prepare(args):
    prior = args.prior_packet.resolve(strict=True)
    require(
        digest(prior / "Trial.json")
        == "944ff0fb4eb3a4d58ce560975e155ca212238960ff77d59c8ac3c2c496052ade"
        and digest(prior / "Result.json")
        == "9ce16e3107f58a0262a26447ec1d882ed86449ac245151c49ee70335e757f251",
        "the exact prior native source trial changed",
    )
    old = json.loads((prior / "Trial.json").read_bytes())
    result = json.loads((prior / "Result.json").read_bytes())
    author = result["phases"]["Author"]
    reopen = result["phases"]["Reopen"]
    require(
        result["passed"] is False
        and result["controls_healthy"] is True
        and result["distinct_processes"] == 4
        and author["passed"] is True
        and author["preference_restored"] is True
        and author["captured_original_preference"] is True
        and reopen["passed"] is False
        and reopen["fresh_reopen_preference"] is True
        and reopen["immutable_inputs_unchanged"] is True,
        "prior true-setting outcome and restoration must remain explicit",
    )
    saved = json.loads((prior / "SavedAuthor.json").read_bytes())
    require(
        digest(prior / "SavedAuthor.json") == author["saved_author_sha256"]
        and saved["occurrence_ids"] == [24, 25]
        and saved["saved_files"]["parent"]["sha256"]
        == "481a13c6f3c068d6df56521b7b0bb31c63f13404dbc0e2f469b0ca6d4034c83c"
        and saved["saved_files"]["child"]["sha256"]
        == "3a39ac65c61cad230c36b27d53f7179813e68afabff2090e1ca98bdd08b2d16f",
        "the actual saved pair or occurrence IDs changed",
    )
    prior_guest = PureWindowsPath(args.prior_guest_root)
    guest = PureWindowsPath(args.guest_root)
    output = args.output.resolve()
    require(
        prior_guest.is_absolute()
        and guest.is_absolute()
        and guest.name == output.name
        and not output.exists(),
        "choose an unused exact host/guest packet",
    )
    native_sources = {}
    for role in ("parent", "child"):
        native = PureWindowsPath(saved[role + "_path"])
        require(
            native.is_relative_to(prior_guest),
            "saved source is outside the declared original guest root",
        )
        relative = native.relative_to(prior_guest)
        host = prior.joinpath(*relative.parts)
        expected = saved["saved_files"][role]["sha256"]
        require(
            host.is_file() and digest(host) == expected,
            "actual same-path native source changed",
        )
        native_sources[role] = {
            "host": str(host),
            "guest": str(native),
            "sha256": expected,
        }
    output.mkdir(parents=True)
    for relative, expected in old["files_sha256"].items():
        copy_checked(prior / relative, output / relative, expected)
    for name in (
        "ReadOnlyNamePreferenceLease.py",
        "InspectComponentNameReadOnly01.py",
        Path(__file__).name,
    ):
        source = Path(__file__).resolve().parent / name
        copy_checked(source, output / "Tools" / name, digest(source))
    for relative in (
        "SavedAuthor.json",
        "Inspection/Author/Result.json",
        "Inspection/Reopen/Result.json",
    ):
        target = (
            "SavedAuthor.json"
            if relative == "SavedAuthor.json"
            else relative.split("/")[1] + "Result.json"
        )
        copy_checked(
            prior / relative, output / "Custody" / target, digest(prior / relative)
        )
    for row in native_sources.values():
        source = Path(row["host"])
        copy_checked(source, output / "Snapshots" / source.name, row["sha256"])
    write_json(
        output / "ReadOnlyAuthorization.json",
        {
            "schema": "kit.sw2026.component-name-readonly-authorization.v1",
            "scope": "temporary false preference in one owned read-only observation process only",
            "original_true_required": True,
            "preference_enum": 18,
            "document_setter_calls": 0,
            "parameter_edits": 0,
            "file_saves": 0,
            "name_setter_calls": 0,
            "same_original_native_paths_required": True,
            "snapshots_are_custody_only": True,
            "durable_capture_and_armed_receipts_before_mutation": True,
            "finally_restore_and_readback_required": True,
            "recovery": "only exact captured/armed original true value, fresh verified owned oracle and no surviving CAD process",
            "supersedes_for_this_observation_only": "original Intent.json preference_policy.changes_authorized",
        },
    )
    write_json(
        output / "PriorTrueFailure.json",
        {
            "schema": "kit.sw2026.component-name-original-setting-failure.v1",
            "result_sha256": digest(prior / "Result.json"),
            "author_result_sha256": digest(prior / "Inspection/Author/Result.json"),
            "reopen_result_sha256": digest(prior / "Inspection/Reopen/Result.json"),
            "reopen_recorder_sha256": digest(prior / "Inspection/Reopen/Record.json"),
            "author_passed": True,
            "author_numeric_checks": 30,
            "fresh_reopen_passed": False,
            "controls_healthy": True,
            "distinct_processes": 4,
            "saved_names": ["AuthoredAxisA-1", "AuthoredAxisB-2"],
            "observed_true_setting_names": [
                "IndependentNameCylinder-1",
                "IndependentNameCylinder-2",
            ],
            "native_acceptance": False,
        },
    )
    job = {
        "schema": "kit.sw2026.component-name-readonly-policy.v1",
        "roles": ["ControlBefore", "ReopenFalse", "ControlAfter"],
        "guest_runtime": old["guest_runtime"],
        "native_sources": native_sources,
        "original_preference_required": True,
        "temporary_preference": False,
        "file_saves": 0,
        "document_setter_calls": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "files_sha256": {
            path.relative_to(output).as_posix(): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
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
        str(guest / "Tools/InspectComponentNameReadOnly01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.component-name-readonly-policy-recipe.v1",
        "packet_sha256": trial_sha,
        "scope": "same-file read-only false-setting discriminator; no source authoring, save or document setter",
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
            str(output / "Tools/InspectComponentNameReadOnly01.py"),
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
                "source_control_must_pass_first": role == "ReopenFalse",
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
        "recovery_condition": "owned observation process died or restoration failed; exact captured+armed original true receipts and independently idle oracle required",
        "recovery_opens_native_documents": False,
        "recovery_requires_current_source_files": False,
        "host_recovery_verify_argv": [
            "uv",
            "run",
            "--no-project",
            "--offline",
            "--isolated",
            "--python",
            "3.11",
            "python",
            "-B",
            str(output / "Tools/InspectComponentNameReadOnly01.py"),
            "verify-recovery",
            str(output / "Trial.json"),
            "--trial-sha256",
            trial_sha,
        ],
        "durable_preference_directory": str(
            guest / "Inspection/ReopenFalse/Preference"
        ),
        "control_after_independent": True,
        "source_commit_before_native_required": True,
        "progress_result": str(guest / "Result.json"),
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }
    write_json(output / "Recipe.json", recipe)
    return {
        "packet": str(output),
        "trial_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "frozen_files": len(job["files_sha256"]),
        "native_processes_started": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-packet", type=Path, required=True)
    parser.add_argument("--prior-guest-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
