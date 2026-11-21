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
        "base-name input changed: " + source.name,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "base-name frozen destination already exists")
    copyfile(source, target)
    require(digest(target) == expected, "base-name frozen copy differs")


def prepare(args):
    prior = args.prior_packet.resolve(strict=True)
    require(
        digest(prior / "Trial.json")
        == "4fbd3b22ea882e67585eb5450f42204fed8547ab2d09cbc76b8362c2ed90a2c5"
        and digest(prior / "Result.json")
        == "da64946316bcea15fa51d1dd3662994b8f3ca23ecff9ade283b906f3e0886800"
        and digest(prior / "Inspection/Author/Record.json")
        == "de627bf51e636753f9d66601aeff33ac398dc222b10e5b2541075fd8a91edd0b",
        "the controlled suffix failure changed",
    )
    old = json.loads((prior / "Trial.json").read_bytes())
    failed = json.loads((prior / "Result.json").read_bytes())
    author = failed["phases"]["Author"]
    require(
        failed["passed"] is False
        and failed["controls_healthy"] is True
        and failed["distinct_processes"] == 3
        and author["preference_restored"] is True
        and author["captured_original_preference"] is True,
        "the prior failed attempt must retain healthy controls and restoration",
    )
    raw = json.loads((prior / "Inspection/Author/Record.json").read_bytes())
    observed = raw["rename_observations"]
    require(
        len(observed) == 1
        and observed[0]["setter_input"] == "AuthoredAxisA-1"
        and observed[0]["before"] == "IndependentNameCylinder-1"
        and observed[0]["after"] == "AuthoredAxisA-1-1"
        and observed[0]["native_id"] == observed[0]["selected_component_id"],
        "the exact recorded instance-suffix discriminator changed",
    )
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(
        not output.exists() and guest.is_absolute() and guest.name == output.name,
        "choose an unused base-name packet",
    )
    output.mkdir(parents=True)
    for relative, expected in old["files_sha256"].items():
        copy_checked(prior / relative, output / relative, expected)
    for name in ("InspectCustomComponentBaseName01.py", Path(__file__).name):
        source = Path(__file__).resolve().parent / name
        copy_checked(source, output / "Tools" / name, digest(source))
    require(
        digest(args.source_record) == args.source_sha256,
        "the exact-build setter source record changed",
    )
    copy_checked(args.source_record, output / "SetterSource.json", args.source_sha256)
    copy_checked(
        args.prediction_file,
        output / "FrozenPrediction01.json",
        "2ed860d27f02eafb59f8e34d672ab68d9b071d9e94d35f3b6bd72badaf78ba90",
    )
    write_json(
        output / "SuffixFailure.json",
        {
            "schema": "kit.sw2026.component-name-suffix-failure.v1",
            "result_sha256": digest(prior / "Result.json"),
            "author_record_sha256": digest(prior / "Inspection/Author/Record.json"),
            "controls_healthy": True,
            "distinct_processes": 3,
            "prior_rename": observed,
            "first_failure_stage": raw["first_failure"]["stage"],
            "preference_original": True,
            "preference_restored": True,
            "saved_custom_parent": False,
            "writer_outputs": 0,
            "native_acceptance": False,
        },
    )
    job = {
        **old,
        "name_setter_method": "base-name-with-unchanged-authored-full-name-predicate",
        "prior_retry_trial_sha256": digest(prior / "Trial.json"),
        "prior_retry_result_sha256": digest(prior / "Result.json"),
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
        str(guest / "Tools/InspectCustomComponentBaseName01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.custom-component-base-name-recipe.v1",
        "packet_sha256": trial_sha,
        "scope": "same independent full-name intent; only Name2 base input and pre-gate matched observations change",
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
            str(output / "Tools/InspectCustomComponentBaseName01.py"),
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
        "recovery_condition": "owned author process dead and oracle idle; exact packet durable Captured.json required",
        "durable_preference_directory": str(guest / "Inspection/Author/Preference"),
        "source_commit_before_native_required": True,
        "progress_result": str(guest / "Result.json"),
        "control_after_independent": True,
        "heldout_inputs_read": 0,
        "native_processes_started": 0,
        "writer_outputs": 0,
    }
    write_json(output / "Recipe.json", recipe)
    return {
        "packet": str(output),
        "trial_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "frozen_files": len(job["files_sha256"]),
        "original_prediction_unchanged": digest(output / "FrozenPrediction01.json")
        == digest(args.prediction_file),
        "preference_lease_unchanged": digest(
            output / "Tools/ComponentNamePreferenceLease.py"
        )
        == digest(prior / "Tools/ComponentNamePreferenceLease.py"),
        "native_processes_started": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-packet", type=Path, required=True)
    parser.add_argument("--source-record", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--prediction-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
