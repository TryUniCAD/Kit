import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))
import InspectCustomComponentNames01 as original
from CaptureComponentNameSetterApi01 import capture as capture_api
from ComponentNamePreferenceLease import PreferenceLease, durable

baseline = original.baseline
ROLES = ("ControlBefore", "Author", "Reopen", "ControlAfter")
BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"
CAPTURE = original.capture_state


def observed_capture(author, model, child_path, wanted, ids):
    row = original.name_probe.names(author, model, child_path)
    row["expected_names"] = [item["name"] for item in wanted["occurrences"]]
    author.rec.data.setdefault("matched_names_before_strict_capture", []).append(row)
    author.rec.flush()
    return CAPTURE(author, model, child_path, wanted, ids)


original.capture_state = observed_capture


def verify(path, expected):
    baseline.require(
        baseline.digest(path) == expected, "owned preference retry changed"
    )
    job = json.loads(path.read_bytes())
    baseline.require(
        path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools"
        and job["schema"] == "kit.sw2026.custom-component-name-preference-retry.v1"
        and job["roles"] == list(ROLES)
        and job["heldout_inputs_read"] == job["writer_outputs"] == 0
        and job["native_acceptance"] is False
        and job["temporary_preference_change_authorized"] is True
        and job["reopen_under_captured_original_setting"] is True,
        "owned preference retry scope differs",
    )
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    baseline.verify(ROOT / "Baseline/Trial.json", BASE_TRIAL)
    plan = json.loads((ROOT / "Intent.json").read_bytes())
    baseline.require(
        baseline.digest(ROOT / "Intent.json")
        == "0faaef5ff9bfaf0fb8e2573f758d41ffce6502c4cc93ee3a75006c956a8eb612"
        and job["superseded_intent_field"] == "preference_policy.changes_authorized"
        and job["temporary_preference_enum"] == 18,
        "geometry/name intent or narrow preference authorization differs",
    )
    return job, plan


def runtime_matches(job):
    runtime = job["guest_runtime"]
    baseline.require(
        os.name == "nt"
        and tuple(sys.version_info[:3])
        == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "owned preference retry requires the pinned guest runtime",
    )
    expected_api = json.loads((ROOT / "ApiMetadata.json").read_bytes())
    baseline.require(
        capture_api() == expected_api,
        "actual registered preference setter metadata changed",
    )


def phase(path, expected, role):
    baseline.require(
        os.name == "nt" and role in ROLES, "only root runs the owned native retry"
    )
    job, plan = verify(path, expected)
    runtime_matches(job)
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    if role.startswith("Control"):
        row = baseline.phase(ROOT / "Baseline/Trial.json", BASE_TRIAL, "Feature", role)
        result = {
            "role": role,
            "passed": row["passed"],
            "control": row,
            "oracle_identity": row.get("oracle_identity"),
            "numeric_checks": row.get("numeric_checks", 0),
            "native_acceptance": False,
            "preference_setter_calls": 0,
        }
        baseline.write_json(directory / "Result.json", result)
        return result
    before = json.loads((ROOT / "Inspection/ControlBefore/Result.json").read_bytes())
    baseline.require(
        before["control"]["passed"] is True, "retry control-before has not passed"
    )
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
        "parameter_edits": 0,
        "preference_setter_calls": 0,
    }
    controller = author = lease = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle owned-preference oracle", Swapp.sweep)
            controller = recorder.call("start fresh owned-preference oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact owned-preference oracle",
                application_identity,
                controller.app,
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "unexpected owned-preference oracle",
            )
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            baseline.require(
                int(author.get(controller.app, "GetDocumentCount")) == 0,
                "owned-preference retry is not cold",
            )
            wanted = original.prediction(plan)
            if role == "Author":
                lease = PreferenceLease(
                    author, directory / "Preference", expected, identity
                )
                result["captured_original_preference"] = lease.begin()
                result.update(
                    original.author_control(author, controller, plan, wanted, 18)
                )
                result["saved_author_sha256"] = baseline.digest(
                    ROOT / "SavedAuthor.json"
                )
            else:
                prior = json.loads(
                    (ROOT / "Inspection/Author/Result.json").read_bytes()
                )
                baseline.require(
                    prior["passed"] is True and prior["preference_restored"] is True,
                    "source authoring and original-setting restoration must pass first",
                )
                current = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
                result["captured_original_preference"] = prior[
                    "captured_original_preference"
                ]
                result["fresh_reopen_preference"] = current
                baseline.require(
                    current == prior["captured_original_preference"],
                    "fresh reopen did not start under the actual captured original setting",
                )
                result.update(original.reopen_control(author, controller, plan, wanted))
                after = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
                result["fresh_reopen_preference_after"] = after
                baseline.require(
                    after == current,
                    "fresh reopen changed the original application setting",
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
                    result["preference_setter_calls"] = lease.setter_calls
                    result["captured_original_preference"] = lease.original
                except Exception as error:
                    result["preference_restored"] = False
                    result["recovery_required"] = True
                    recorder.failure(error, cleanup=True)
                finally:
                    result["preference_setter_calls"] = lease.setter_calls
                    result["captured_original_preference"] = lease.original
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
        and (role != "Author" or result.get("preference_restored") is True)
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


def recover(path, expected, output):
    job, _ = verify(path, expected)
    runtime_matches(job)
    output = output.resolve()
    baseline.require(
        output.is_relative_to(ROOT) and not output.exists(),
        "recovery output must be unused within this packet",
    )
    captured = json.loads(
        (ROOT / "Inspection/Author/Preference/Captured.json").read_bytes()
    )
    baseline.require(
        captured["schema"] == "kit.sw2026.component-name-preference-lease.v1"
        and captured["packet_sha256"] == expected
        and captured["preference_enum"] == 18
        and type(captured["original_value"]) is bool
        and captured["oracle_identity"]["sha256"] == baseline.ORACLE,
        "preference recovery requires this exact owned durable capture",
    )
    from AuthorCurves import CurveAuthor, Recorder
    from OracleIdentity import application_identity
    import Swapp

    output.mkdir(parents=True)
    recorder = Recorder(
        output / "Record.json", {"role": "Recovery", "packet_sha256": expected}
    )
    result = {
        "passed": False,
        "restored": False,
        "native_acceptance": False,
        "preference_enum": 18,
        "original_value": captured["original_value"],
        "preference_setter_calls": 0,
        "writer_outputs": 0,
    }
    controller = None
    try:
        recorder.call(
            "require no surviving or foreign CAD process before recovery", Swapp.sweep
        )
        controller = recorder.call("start fresh owned preference recovery", Swapp.Sw)
        identity = recorder.call(
            "verify exact preference recovery oracle",
            application_identity,
            controller.app,
        )
        baseline.require(
            identity["sha256"] == baseline.ORACLE
            and identity["version_matches"]
            and identity["file_version"] == "34.5.2.0604",
            "unexpected preference recovery oracle",
        )
        result["oracle_identity"] = identity
        author = CurveAuthor(controller.app, recorder, Swapp)
        baseline.require(
            int(author.get(author.app, "GetDocumentCount")) == 0,
            "recovery must have no documents",
        )
        before = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
        durable(
            output / "Before.json",
            {
                "packet_sha256": expected,
                "actual_value": before,
                "restore_target": captured["original_value"],
                "oracle_identity": identity,
            },
        )
        if before != captured["original_value"]:
            result["preference_setter_calls"] += 1
            result["setter_return"] = author.get(
                author.app, "SetUserPreferenceToggle", 18, captured["original_value"]
            )
        result["actual_value"] = bool(
            author.get(author.app, "GetUserPreferenceToggle", 18)
        )
        result["restored"] = result["actual_value"] == captured["original_value"]
        durable(output / "After.json", {"packet_sha256": expected, **result})
        baseline.require(
            result["restored"],
            "recovery did not restore the actual captured original setting",
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
        source = ROOT / "Inspection" / role / "Result.json"
        if source.is_file():
            rows[role] = json.loads(source.read_bytes())
    identities = {
        (row.get("oracle_identity") or {}).get("process_creation_filetime")
        for row in rows.values()
    } - {None}
    healthy = all(
        rows.get(role, {}).get("control", {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    passed = bool(
        healthy
        and len(rows) == len(identities) == 4
        and all(row.get("passed") for row in rows.values())
        and rows["Author"].get("preference_restored") is True
        and rows["Reopen"].get("fresh_reopen_preference")
        == rows["Author"].get("captured_original_preference")
    )
    result = {
        "schema": "kit.sw2026.custom-component-name-preference-retry-result.v1",
        "passed": passed,
        "source_control_qualified": passed,
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "phases": rows,
        "original_preference_restored": rows.get("Author", {}).get(
            "preference_restored"
        )
        is True,
        "fresh_reopen_under_original_setting": bool(
            rows.get("Reopen", {}).get("passed")
            and rows["Reopen"].get("fresh_reopen_preference")
            == rows.get("Author", {}).get("captured_original_preference")
        ),
        "native_acceptance": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
    }
    baseline.write_json(ROOT / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary", "recover"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase", choices=ROLES)
    parser.add_argument("--recovery-output", type=Path)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        _, plan = verify(path, args.trial_sha256)
        original.prediction(plan)
        print(
            json.dumps(
                {
                    "verified": True,
                    "native_processes_started": 0,
                    "heldout_inputs_read": 0,
                }
            )
        )
        return 0
    if args.command == "recover":
        baseline.require(
            args.recovery_output is not None,
            "recovery requires its unused output directory",
        )
        result = recover(path, args.trial_sha256, args.recovery_output)
    else:
        result = (
            phase(path, args.trial_sha256, args.phase)
            if args.command == "phase"
            else summary(path, args.trial_sha256)
        )
    print(json.dumps({"passed": result["passed"], "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
