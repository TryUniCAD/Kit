import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import runpy
from shutil import copyfile


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def copy_checked(source, target, expected):
    require(
        source.is_file() and not source.is_symlink() and digest(source) == expected,
        "the disclosed frozen source changed: " + source.name,
    )
    require(not target.exists(), "the frozen destination already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    copyfile(source, target)
    require(digest(target) == expected, "the frozen copy differs")


def prepare(args):
    source = args.source_packet.resolve(strict=True)
    ambient = args.ambient_packet.resolve(strict=True)
    working = args.generated_host_root.resolve(strict=True)
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(
        not output.exists() and guest.is_absolute() and guest.name == output.name,
        "choose an unused exact host and guest packet root",
    )
    require(
        digest(source / "Trial.json")
        == "a1dd46620b5ba350eccead37510ac103343167a2dfd426b4fde541ee53e5682c"
        and digest(source / "Result.json")
        == "43e841e9f1d627e3ad077629ec8ffbd931ada6acb3b442e229f6a371303a5780"
        and digest(ambient / "Trial.json")
        == "01b767e56dd5f8dd2f1a2c5218a0003b98654f7b9f4eea27369464575172fcd8"
        and digest(ambient / "Result.json")
        == "e565f5e940076262507fff43296ee1205ccd7fbcfb8eee6ad2ca92d36b6998fa",
        "the declared native source or warning-free generated evidence changed",
    )
    old_source = json.loads((source / "Trial.json").read_bytes())
    old_ambient = json.loads((ambient / "Trial.json").read_bytes())
    generated = {}
    for kind in ("parent", "child"):
        native = PureWindowsPath(old_ambient["working_" + kind + "_guest_path"])
        host = working / native.name
        frozen = old_ambient["variants"]["On"][kind]
        require(
            host.name == Path(frozen["file"]).name and digest(host) == frozen["sha256"],
            "the original generated working pair is not the exact ambient-on pair",
        )
        generated[kind] = {
            "host": str(host),
            "guest": str(native),
            "sha256": frozen["sha256"],
            "bytes": frozen["bytes"],
        }
    output.mkdir(parents=True)
    for relative, expected in old_source["files_sha256"].items():
        copy_checked(source / relative, output / relative, expected)
    copy_checked(
        source / "Trial.json",
        output / "PriorReadOnlyTrial.json",
        digest(source / "Trial.json"),
    )
    copy_checked(
        source / "Result.json",
        output / "Evidence/ReadOnlyPolicyResult.json",
        digest(source / "Result.json"),
    )
    for relative, expected in old_ambient["files_sha256"].items():
        copy_checked(ambient / relative, output / "AmbientPrior" / relative, expected)
    copy_checked(
        ambient / "Trial.json",
        output / "AmbientPrior/Trial.json",
        digest(ambient / "Trial.json"),
    )
    copy_checked(
        ambient / "Result.json",
        output / "Evidence/ParentAmbientResult.json",
        digest(ambient / "Result.json"),
    )
    for relative in ("GeometryPrediction.json", "Neutral.json"):
        copy_checked(ambient / relative, output / relative, digest(ambient / relative))
    copy_checked(
        ambient / "Tools/InspectConcentricParentAmbient01.py",
        output / "Tools/InspectConcentricParentAmbient01.py",
        "73b2ce157be413be5014e537db21f9d70ab45f1d00c528878c910c57a03f3abc",
    )
    for name in ("InspectGeneratedNamePolicy01.py", Path(__file__).name):
        origin = Path(__file__).resolve().parent / name
        copy_checked(origin, output / "Tools" / name, digest(origin))
    job = {
        "schema": "kit.sw2026.generated-concentric-name-policy.v1",
        "roles": [
            "TrueControlBefore",
            "TrueGenerated",
            "TrueControlAfter",
            "FalseControlBefore",
            "FalseGenerated",
            "FalseControlAfter",
        ],
        "guest_runtime": old_source["guest_runtime"],
        "generated_sources": generated,
        "native_false_controls": old_source["native_sources"],
        "true_controls": "original disclosed D01 from the exact Baseline/Trial.json",
        "child_definition_name": "NeutralCylinderAlphaDerived",
        "occurrence_ids": [17, 18],
        "original_preference_required": True,
        "temporary_preference": False,
        "file_saves": 0,
        "document_setter_calls": 0,
        "parameter_edits": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "scope": "same exact warning-free generated pair; separately bracketed actual true normalization and scoped readonly false authored-name preservation; no document edits or saves",
    }
    module = runpy.run_path(
        str(output / "Tools/InspectGeneratedNamePolicy01.py"),
        run_name="freeze_predictions",
    )
    for kind, value in module["predictions"](job).items():
        write_json(output / ("Prediction" + kind.title() + ".json"), value)
    write_json(
        output / "NamePolicyAuthorization.json",
        {
            "schema": "kit.sw2026.generated-concentric-name-policy-authorization.v1",
            "original_true_required": True,
            "preference_enum": 18,
            "ordinary_true_branch_setter_calls": 0,
            "false_branch": "one separate readonly false lease in each of two native source controls and the generated observation",
            "durable_capture_and_armed_before_mutation": True,
            "restore_actual_original_and_readback_in_finally": True,
            "read_only_open_required": True,
            "document_setter_calls": 0,
            "file_saves": 0,
            "parameter_edits": 0,
            "name_setter_calls": 0,
            "native_sources_and_generated_files_are_independent": True,
            "generated_original_locators_and_hashes_unchanged": True,
            "normalization_grade_is_not_authored_name_preservation": True,
            "unchanged_original_prediction_required": "AmbientPrior/Baseline/Evidence/FeaturePrediction.json",
            "all_heldout_inputs_excluded": True,
        },
    )
    write_json(
        output / "ExpectationProvenance.json",
        {
            "schema": "kit.sw2026.generated-name-policy-prediction-provenance.v1",
            "original_neutral_sha256": digest(output / "Neutral.json"),
            "original_feature_prediction_sha256": digest(
                output / "Baseline/Evidence/FeaturePrediction.json"
            ),
            "independent_ambient_intent_sha256": digest(
                output / "AmbientPrior/AmbientIntent.json"
            ),
            "geometry_prediction_sha256": digest(output / "GeometryPrediction.json"),
            "authored_name_rule": "unchanged independently authored ComponentInstance.name, original occurrence order and ordinal",
            "true_normalization_rule": "actual shared part ComponentDefinition.name followed by the independently authored ordinal; applies only to this measured ordinary true-setting diagnostic",
            "native_true_original_failure_sha256": digest(
                output / "Custody/ReopenResult.json"
            ),
            "native_false_source_pass_sha256": digest(
                output / "Evidence/ReadOnlyPolicyResult.json"
            ),
            "generated_true_ambient_observation_sha256": digest(
                output / "Evidence/ParentAmbientResult.json"
            ),
            "full_tree_rule": "original full 25-row parent; substitute names only on the two Reference rows for normalization; original child defaults replaced by the independent one-ambient intent, retaining all other rows",
            "parent_tree_rows": 25,
            "child_tree_rows": 22,
            "names_and_geometry_not_fitted_to_a_new_run": True,
            "false_generated_native_observation_pending": True,
            "native_acceptance": False,
        },
    )
    job["files_sha256"] = {
        path.relative_to(output).as_posix(): digest(path)
        for path in sorted(output.rglob("*"))
        if path.is_file()
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
        str(guest / "Tools/InspectGeneratedNamePolicy01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--trial-sha256", trial_sha]
    host = [
        "uv",
        "run",
        "--no-project",
        "--offline",
        "--isolated",
        "--python",
        "3.11",
        "python",
        "-B",
        str(output / "Tools/InspectGeneratedNamePolicy01.py"),
    ]
    host_tail = [str(output / "Trial.json"), "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.generated-concentric-name-policy-recipe.v1",
        "packet_sha256": trial_sha,
        "scope": job["scope"],
        "host_verify_argv": [*host, "verify", *host_tail],
        "host_contract_argv": [*host, "contract", *host_tail],
        "host_recovery_verify_argv": [*host, "verify-recovery", *host_tail],
        "guest_verify_argv": [*prefix, "verify", *tail],
        "guest_contract_argv": [*prefix, "contract", *tail],
        "commands": [
            {
                "role": role,
                "argv": [*prefix, "phase", *tail, "--phase", role],
                "always_run_after_other_failure": role.endswith("ControlAfter"),
                "healthy_bracket_required": not role.endswith("ControlAfter")
                and role != "TrueControlBefore",
            }
            for role in job["roles"]
        ],
        "summary_argv": [*prefix, "summary", *tail],
        "recovery_by_phase": {
            role: {
                "argv": [
                    *prefix,
                    "recover",
                    *tail,
                    "--phase",
                    role,
                    "--recovery-output",
                    str(guest / ("Recovery" + role + "01")),
                ],
                "durable_lease_directory": str(
                    guest / "Inspection" / role / "Preference"
                ),
            }
            for role in job["roles"]
            if role.startswith("False")
        },
        "recovery_precondition": "exact captured and armed original true lease, owned process gone and independently idle oracle; do not close any foreign process",
        "recovery_opens_documents": False,
        "recovery_requires_current_native_files": False,
        "source_commit_before_native_required": True,
        "original_locator_files_must_already_match": True,
        "materialization_or_overwrite_step": None,
        "controls_are_native_sources_and_not_generated_snapshots": True,
        "native_processes_planned": 6,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "terminal_result": str(guest / "Result.json"),
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
    parser.add_argument("--source-packet", type=Path, required=True)
    parser.add_argument("--ambient-packet", type=Path, required=True)
    parser.add_argument("--generated-host-root", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
