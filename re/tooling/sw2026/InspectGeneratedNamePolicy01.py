import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import InspectComponentNameReadOnly01 as native_source
import InspectConcentricParentAmbient01 as ambient
from ComponentNamePreferenceLease import durable
from ReadOnlyNamePreferenceLease import ReadOnlyNamePreferenceLease

ROOT = Path(__file__).resolve().parent.parent
baseline = native_source.baseline
ROLES = (
    "TrueControlBefore",
    "TrueGenerated",
    "TrueControlAfter",
    "FalseControlBefore",
    "FalseGenerated",
    "FalseControlAfter",
)
READONLY_TRIAL = "a1dd46620b5ba350eccead37510ac103343167a2dfd426b4fde541ee53e5682c"
AMBIENT_TRIAL = "01b767e56dd5f8dd2f1a2c5218a0003b98654f7b9f4eea27369464575172fcd8"
READONLY_RESULT = "43e841e9f1d627e3ad077629ec8ffbd931ada6acb3b442e229f6a371303a5780"
AMBIENT_RESULT = "e565f5e940076262507fff43296ee1205ccd7fbcfb8eee6ad2ca92d36b6998fa"
SCHEMA = "kit.sw2026.generated-concentric-name-policy.v1"


def generated_sources(job):
    domain = "guest" if os.name == "nt" else "host"
    return {key: Path(row[domain]) for key, row in job["generated_sources"].items()}


def predictions(job):
    previous = json.loads((ROOT / "AmbientPrior/Trial.json").read_bytes())
    authored = ambient.prediction(previous, "On")
    neutral = json.loads((ROOT / "Neutral.json").read_bytes())["assembly"]
    instances = neutral["instances"]["$tuple"]
    definitions = neutral["definitions"]["$tuple"]
    baseline.require(
        len(instances) == len(authored["occurrences"]) == 2
        and [row["name"] for row in instances]
        == [row["name"] for row in authored["occurrences"]]
        == ["Cylinder-1", "Cylinder-2"]
        and len({row["definition_id"] for row in instances}) == 1
        and all(row["reference_number"] == "" for row in instances),
        "the original independently authored occurrence intent changed",
    )
    (child,) = [
        row for row in definitions if row["id"] == instances[0]["definition_id"]
    ]
    baseline.require(
        child["kind"] == "part"
        and child["name"] == job["child_definition_name"]
        and job["occurrence_ids"] == [17, 18],
        "the original actual child definition or occurrence IDs changed",
    )
    normalized = deepcopy(authored)
    replacements = {}
    for index, row in enumerate(authored["occurrences"], 1):
        base, separator, ordinal = row["name"].rpartition("-")
        baseline.require(
            base and separator and ordinal == str(index), "ordinal changed"
        )
        replacements[row["name"]] = child["name"] + "-" + ordinal
    for row in normalized["occurrences"]:
        row["name"] = replacements[row["name"]]
    references = [row for row in normalized["tree"] if row[1] == "Reference"]
    baseline.require(
        [row[0] for row in references] == list(replacements),
        "the complete authored parent reference order changed",
    )
    for row in references:
        row[0] = replacements[row[0]]
    baseline.require(
        len(authored["tree"]) == len(normalized["tree"]) == 25
        and len(authored["child_tree"]) == len(normalized["child_tree"]) == 22,
        "the original full trees or independently authored ambient projection changed",
    )
    return {"authored": authored, "normalized": normalized}


def verify_recovery(path, expected):
    baseline.require(
        baseline.digest(path) == expected
        and path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools",
        "run this exact frozen name-policy observer",
    )
    job = json.loads(path.read_bytes())
    baseline.require(
        job["schema"] == SCHEMA
        and job["roles"] == list(ROLES)
        and job["original_preference_required"] is True
        and job["temporary_preference"] is False
        and job["native_acceptance"] is False
        and job["file_saves"]
        == job["document_setter_calls"]
        == job["parameter_edits"]
        == job["writer_outputs"]
        == job["heldout_inputs_read"]
        == 0,
        "the read-only policy boundary changed",
    )
    for relative, digest in job["files_sha256"].items():
        if relative.endswith(".py") or relative == "ApiMetadata.json":
            baseline.checked(ROOT / relative, digest)
    return job


def verify(path, expected):
    job = verify_recovery(path, expected)
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    original_job, _, wanted, authored = native_source.verify(
        ROOT / "PriorReadOnlyTrial.json", READONLY_TRIAL
    )
    baseline.require(
        job["native_false_controls"] == original_job["native_sources"],
        "the separately declared native false-setting controls changed",
    )
    baseline.checked(ROOT / "AmbientPrior/Trial.json", AMBIENT_TRIAL)
    previous = json.loads((ROOT / "AmbientPrior/Trial.json").read_bytes())
    for relative, digest in previous["files_sha256"].items():
        baseline.checked(ROOT / "AmbientPrior" / relative, digest)
    for relative in ("GeometryPrediction.json", "Neutral.json"):
        baseline.require(
            baseline.digest(ROOT / relative)
            == baseline.digest(ROOT / "AmbientPrior" / relative),
            "the original generated prediction inputs changed",
        )
    baseline.checked(ROOT / "Evidence/ReadOnlyPolicyResult.json", READONLY_RESULT)
    prior = json.loads((ROOT / "Evidence/ReadOnlyPolicyResult.json").read_bytes())
    baseline.require(
        prior["passed"] is True
        and prior["controls_healthy"] is True
        and prior["distinct_processes"] == 3
        and prior["document_setter_calls"] == prior["file_saves"] == 0
        and prior["phases"]["ReopenFalse"]["preference_restored"] is True,
        "the independently measured native false-setting control changed",
    )
    baseline.checked(ROOT / "Evidence/ParentAmbientResult.json", AMBIENT_RESULT)
    measured = json.loads((ROOT / "Evidence/ParentAmbientResult.json").read_bytes())
    baseline.require(
        measured["controls_healthy"] is True
        and measured["distinct_processes"] == 4
        and measured["phases"]["ParentOn"]["open_errors"]
        == measured["phases"]["ParentOn"]["open_warnings"]
        == 0
        and measured["phases"]["ParentOn"]["independent_checks_passed"] is True,
        "the prior warning-free generated pair evidence changed",
    )
    for kind, native in generated_sources(job).items():
        frozen = previous["variants"]["On"][kind]
        baseline.require(
            job["generated_sources"][kind]["sha256"] == frozen["sha256"]
            and job["generated_sources"][kind]["guest"]
            == previous["working_" + kind + "_guest_path"],
            "the exact original generated locator or identity changed",
        )
        baseline.checked(native, frozen["sha256"])
    expected_states = predictions(job)
    for kind, value in expected_states.items():
        baseline.require(
            value
            == json.loads(
                (ROOT / ("Prediction" + kind.title() + ".json")).read_bytes()
            ),
            "the predeclared independent name/tree/geometry expectation changed",
        )
    return job, original_job, wanted, authored, expected_states


def names_match(observation, names, ids):
    rows = observation["reference_names"]["references"]
    actual = {row["component_id"]: row for row in rows}
    return bool(
        observation["reference_names"]["observation_complete"]
        and len(actual) == len(ids) == len(rows) == 2
        and set(actual) == set(ids)
        and all(
            actual[native_id]["component_name2"] == name
            and actual[native_id]["feature_name"] == name
            and actual[native_id]["component_path_matches_actual_child"]
            and actual[native_id]["repeated_component_read_stable"]
            and actual[native_id]["repeated_feature_read_stable"]
            for native_id, name in zip(ids, names, strict=True)
        )
    )


def generated_observe(author, controller, job, expected_states, temporary):
    paths = generated_sources(job)
    model, errors, warnings = author.rec.call(
        "read-only open exact warning-free generated pair at original locators",
        controller.open,
        str(paths["parent"]),
        2,
        read_only=True,
    )
    author.rec.data["read_only_open"] = {
        "errors": errors,
        "warnings": warnings,
        "document_returned": model is not None,
        "read_only_requested": True,
        "expected_preference": not temporary,
        "exact_parent": str(paths["parent"]),
        "exact_child": str(paths["child"]),
    }
    author.rec.flush()
    baseline.require(
        model is not None
        and errors == warnings == 0
        and baseline.same_file(author.get(model, "GetPathName"), paths["parent"]),
        "the exact generated pair failed, warned or opened a foreign document",
    )
    chosen = expected_states["authored" if temporary else "normalized"]
    observations = []
    author.rec.data["policy_observations"] = observations
    for stage in ("initial", "rebuilt"):
        if stage == "rebuilt":
            baseline.require(
                bool(author.get(model, "ForceRebuild3", False)),
                "read-only generated assembly rebuild failed",
            )
        value = ambient.observe(
            author, model, paths["child"], chosen, job["occurrence_ids"]
        )
        value["stage"] = stage
        value["authored_names_preserved"] = names_match(
            value,
            [row["name"] for row in expected_states["authored"]["occurrences"]],
            job["occurrence_ids"],
        )
        value["normalized_names_observed"] = names_match(
            value,
            [row["name"] for row in expected_states["normalized"]["occurrences"]],
            job["occurrence_ids"],
        )
        observations.append(value)
        author.rec.flush()
        baseline.require(
            value["independent_checks_passed"]
            and value["strict_original_capture"]["passed"]
            and value["authored_names_preserved"] is temporary
            and value["normalized_names_observed"] is (not temporary),
            "the distinct predeclared naming, warning, tree, geometry or mate gate failed",
        )
        state = value["strict_original_capture"]["value"]
        baseline.require(
            [row["native_id"] for row in state["occurrences"]] == job["occurrence_ids"]
            and [
                row["occurrence_native_id"]
                for row in state["mate"]["ordered_endpoints"]
            ]
            == job["occurrence_ids"],
            "the actual resolved occurrence or selected mate face owner order changed",
        )
    baseline.require(
        baseline.signature(observations[0]["strict_original_capture"]["value"])
        == baseline.signature(observations[1]["strict_original_capture"]["value"]),
        "the read-only rebuild changed the observed native state",
    )
    return {
        "open_errors": errors,
        "open_warnings": warnings,
        "initial": observations[0],
        "rebuilt": observations[1],
        "authored_name_gate_passed": temporary,
        "normalization_predicate_passed": not temporary,
    }


def require_before(role):
    needed = {
        "TrueGenerated": ("TrueControlBefore",),
        "FalseControlBefore": (
            "TrueControlBefore",
            "TrueGenerated",
            "TrueControlAfter",
        ),
        "FalseGenerated": ("FalseControlBefore",),
    }.get(role, ())
    for previous in needed:
        value = json.loads(
            (ROOT / "Inspection" / previous / "Result.json").read_bytes()
        )
        baseline.require(
            value.get("passed") is True,
            "required healthy preceding phase missing: " + previous,
        )


def phase(path, expected, role):
    baseline.require(os.name == "nt" and role in ROLES, "root owns the native phases")
    job, original_job, wanted, authored, expected_states = verify(path, expected)
    native_source.prior.runtime_matches(job)
    require_before(role)
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    if role in ("TrueControlBefore", "TrueControlAfter"):
        old_role = role.removeprefix("True")
        row = baseline.phase(
            ROOT / "Baseline/Trial.json",
            native_source.prior.BASE_TRIAL,
            "Feature",
            old_role,
        )
        result = {
            "role": role,
            "passed": row["passed"],
            "control": row,
            "oracle_identity": row.get("oracle_identity"),
            "numeric_checks": row.get("numeric_checks", 0),
            "native_acceptance": False,
            "preference_setter_calls": 0,
            "file_saves": 0,
            "document_setter_calls": 0,
            "actual_preference_required": True,
        }
        baseline.write_json(directory / "Result.json", result)
        return result
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(
        directory / "Record.json", {"role": role, "packet_sha256": expected}
    )
    result = {
        "role": role,
        "passed": False,
        "native_acceptance": False,
        "writer_outputs": 0,
        "file_saves": 0,
        "document_setter_calls": 0,
        "parameter_edits": 0,
        "preference_setter_calls": 0,
    }
    controller = lease = None
    temporary = role.startswith("False")
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("require idle name-policy oracle", Swapp.sweep)
            controller = recorder.call("start fresh name-policy oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact name-policy oracle", application_identity, controller.app
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "unexpected oracle",
            )
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            baseline.require(
                int(author.get(author.app, "GetDocumentCount")) == 0,
                "name-policy oracle is not cold",
            )
            original = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
            result["captured_original_preference"] = original
            baseline.require(
                original is True, "actual original true setting is required"
            )
            if temporary:
                lease = ReadOnlyNamePreferenceLease(
                    author, directory / "Preference", expected, identity
                )
                lease.begin()
            actual = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
            result["actual_preference_before_open"] = actual
            baseline.require(
                actual is (not temporary), "actual setting differs before observation"
            )
            if role in ("FalseControlBefore", "FalseControlAfter"):
                result.update(
                    native_source.observe(
                        author, controller, original_job, wanted, authored
                    )
                )
            else:
                result.update(
                    generated_observe(
                        author, controller, job, expected_states, temporary
                    )
                )
            result["actual_preference_after_observation"] = bool(
                author.get(author.app, "GetUserPreferenceToggle", 18)
            )
            baseline.require(
                result["actual_preference_after_observation"] is actual,
                "observation changed the measured setting",
            )
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = {"type": type(error).__name__, "error": str(error)}
        finally:
            if lease is not None:
                try:
                    result["preference_restoration"] = lease.restore()
                    result["preference_restored"] = lease.restored
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                    result["preference_restored"] = False
                    result["recovery_required"] = True
                finally:
                    result["preference_setter_calls"] = lease.setter_calls
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    try:
        verify(path, expected)
        result["immutable_inputs_unchanged"] = True
    except Exception as error:
        recorder.failure(error)
        result["immutable_inputs_unchanged"] = False
    result["passed"] = bool(
        result["passed"]
        and result["immutable_inputs_unchanged"]
        and (not temporary or result.get("preference_restored") is True)
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and recorder.data["first_failure"] is None
        and not recorder.data["cleanup_errors"]
    )
    result["numeric_checks"] = len(recorder.data["checks"])
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    baseline.write_json(directory / "Result.json", result)
    return result


def contract(path, expected):
    job, _, _, _, expected_states = verify(path, expected)
    old = json.loads((ROOT / "Evidence/ParentAmbientResult.json").read_bytes())[
        "phases"
    ]["ParentOn"]
    checks = []
    for key in ("before_rebuild", "after_rebuild"):
        value = old[key]
        expected_names = [
            row["name"] for row in expected_states["normalized"]["occurrences"]
        ]
        authored_names = [
            row["name"] for row in expected_states["authored"]["occurrences"]
        ]
        tree = [
            [row["name"], row["type"], row["parent"]]
            for row in value["actual_parent_tree"]["value"]
        ]
        current = {
            "snapshot": key,
            "normalized_names_match": names_match(
                value, expected_names, job["occurrence_ids"]
            ),
            "authored_names_preserved": names_match(
                value, authored_names, job["occurrence_ids"]
            ),
            "full_normalized_tree_matches": tree
            == expected_states["normalized"]["tree"],
            "independent_checks_passed": value["independent_checks_passed"],
        }
        checks.append(current)
        baseline.require(
            current["normalized_names_match"]
            and not current["authored_names_preserved"]
            and current["full_normalized_tree_matches"]
            and current["independent_checks_passed"],
            "prior disclosed observation differs",
        )
    return {
        "verified": True,
        "prior_disclosed_snapshots": checks,
        "prediction_inputs_unchanged": True,
        "false_generated_native_measured": False,
        "native_processes_started": 0,
        "native_acceptance": False,
    }


def recover(path, expected, role, output):
    job = verify_recovery(path, expected)
    baseline.require(
        role.startswith("False") and role in ROLES, "choose one exact false-phase lease"
    )
    native_source.prior.runtime_matches(job)
    output = output.resolve()
    baseline.require(
        output.is_relative_to(ROOT) and not output.exists(),
        "choose an unused recovery output",
    )
    journal = ROOT / "Inspection" / role / "Preference"
    captured = json.loads((journal / "Captured.json").read_bytes())
    armed = json.loads((journal / "Armed.json").read_bytes())
    baseline.require(
        all(
            row["schema"] == "kit.sw2026.component-name-readonly-preference-lease.v1"
            and row["packet_sha256"] == expected
            and row["preference_enum"] == 18
            and row["original_value"] is True
            and row["oracle_identity"]["sha256"] == baseline.ORACLE
            for row in (captured, armed)
        )
        and captured["oracle_identity"] == armed["oracle_identity"]
        and armed["recovery_required_if_no_restored_receipt"] is True,
        "recovery requires this exact owned capture and armed restoration obligation",
    )
    from AuthorCurves import CurveAuthor, Recorder
    from OracleIdentity import application_identity
    import Swapp

    output.mkdir(parents=True)
    recorder = Recorder(
        output / "Record.json",
        {"role": role, "operation": "Recovery", "packet_sha256": expected},
    )
    result = {
        "passed": False,
        "restored": False,
        "file_saves": 0,
        "document_setter_calls": 0,
        "native_acceptance": False,
        "preference_setter_calls": 0,
    }
    controller = None
    try:
        recorder.call("require old owned process gone and oracle idle", Swapp.sweep)
        controller = recorder.call("start fresh name-policy recovery", Swapp.Sw)
        identity = recorder.call(
            "verify exact recovery oracle", application_identity, controller.app
        )
        baseline.require(
            identity["sha256"] == baseline.ORACLE
            and identity["version_matches"]
            and identity["file_version"] == "34.5.2.0604",
            "unexpected recovery oracle",
        )
        author = CurveAuthor(controller.app, recorder, Swapp)
        baseline.require(
            int(author.get(author.app, "GetDocumentCount")) == 0,
            "recovery cannot open documents",
        )
        before = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
        durable(
            output / "Before.json",
            {
                "packet_sha256": expected,
                "actual_value": before,
                "original_value": captured["original_value"],
                "capture_sha256": baseline.digest(journal / "Captured.json"),
                "oracle_identity": identity,
            },
        )
        if before is not True:
            result["preference_setter_calls"] += 1
            result["setter_return"] = author.get(
                author.app, "SetUserPreferenceToggle", 18, True
            )
        result["actual_value"] = bool(
            author.get(author.app, "GetUserPreferenceToggle", 18)
        )
        result["restored"] = result["actual_value"] is captured["original_value"]
        durable(output / "After.json", {"packet_sha256": expected, **result})
        baseline.require(
            result["restored"], "captured original true setting was not restored"
        )
        result["passed"] = True
    except Exception as error:
        recorder.failure(error)
        result["error"] = {"type": type(error).__name__, "error": str(error)}
    finally:
        if controller is not None:
            try:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
            except Exception as error:
                recorder.failure(error, cleanup=True)
    result["passed"] = bool(
        result["passed"]
        and not result.get("controller_diagnostics")
        and not recorder.data["cleanup_errors"]
    )
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    durable(output / "Result.json", result)
    return result


def summary(path, expected):
    verify(path, expected)
    rows = {}
    for role in ROLES:
        filename = ROOT / "Inspection" / role / "Result.json"
        if filename.is_file():
            rows[role] = json.loads(filename.read_bytes())
    identities = {
        (row.get("oracle_identity") or {}).get("process_creation_filetime")
        for row in rows.values()
    } - {None}
    brackets = {}
    for prefix in ("True", "False"):
        brackets[prefix] = all(
            rows.get(prefix + suffix, {}).get("passed") is True
            for suffix in ("ControlBefore", "ControlAfter")
        )
    passed = bool(
        len(identities) == len(rows) == 6
        and all(brackets.values())
        and all(row.get("passed") is True for row in rows.values())
    )
    result = {
        "schema": "kit.sw2026.generated-concentric-name-policy-result.v1",
        "passed": passed,
        "phases": rows,
        "controls_healthy": brackets,
        "distinct_processes": len(identities),
        "numeric_checks": sum(row.get("numeric_checks", 0) for row in rows.values()),
        "authored_name_preserved_in_ordinary_true_setting": rows.get(
            "TrueGenerated", {}
        ).get("authored_name_gate_passed"),
        "false_generated_observation_passed": rows.get("FalseGenerated", {}).get(
            "passed"
        )
        is True,
        "file_saves": 0,
        "document_setter_calls": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
    }
    baseline.write_json(ROOT / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "verify",
            "verify-recovery",
            "contract",
            "phase",
            "summary",
            "recover",
        ),
    )
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase", choices=ROLES)
    parser.add_argument("--recovery-output", type=Path)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.trial_sha256)
        value = {"verified": True, "native_processes_started": 0}
    elif args.command == "verify-recovery":
        verify_recovery(path, args.trial_sha256)
        value = {
            "verified_tools_only": True,
            "native_processes_started": 0,
            "preference_recovery_performed": False,
        }
    elif args.command == "contract":
        value = contract(path, args.trial_sha256)
    elif args.command == "phase":
        baseline.require(args.phase is not None, "phase is required")
        value = phase(path, args.trial_sha256, args.phase)
    elif args.command == "recover":
        baseline.require(
            args.phase is not None and args.recovery_output is not None,
            "exact lease role and recovery output required",
        )
        value = recover(path, args.trial_sha256, args.phase, args.recovery_output)
    else:
        value = summary(path, args.trial_sha256)
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
    return (
        0
        if value.get(
            "passed", value.get("verified", value.get("verified_tools_only", False))
        )
        else 3
    )


if __name__ == "__main__":
    raise SystemExit(main())
