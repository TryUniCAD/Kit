import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import InspectCustomComponentNameRetry01 as prior
from ReadOnlyNamePreferenceLease import ReadOnlyNamePreferenceLease
from ComponentNamePreferenceLease import durable

ROOT = Path(__file__).resolve().parent.parent
original = prior.original
baseline = prior.baseline
ROLES = ("ControlBefore", "ReopenFalse", "ControlAfter")
CONTROL_CAPTURE = baseline.capture


def control_capture(author, *args, **kwargs):
    value = bool(author.get(author.app, "GetUserPreferenceToggle", 18))
    author.rec.data.setdefault("control_name_preference", []).append(value)
    author.rec.flush()
    baseline.require(value is True, "pristine control requires original true setting")
    return CONTROL_CAPTURE(author, *args, **kwargs)


baseline.capture = control_capture


def sources(job):
    domain = "guest" if os.name == "nt" else "host"
    return {key: Path(row[domain]) for key, row in job["native_sources"].items()}


def verify(path, expected):
    baseline.require(
        baseline.digest(path) == expected and path.parent.resolve() == ROOT,
        "read-only name packet identity changed",
    )
    job = json.loads(path.read_bytes())
    baseline.require(
        job["schema"] == "kit.sw2026.component-name-readonly-policy.v1"
        and job["roles"] == list(ROLES)
        and job["original_preference_required"] is True
        and job["temporary_preference"] is False
        and job["file_saves"] == job["document_setter_calls"] == 0
        and job["heldout_inputs_read"] == job["writer_outputs"] == 0
        and job["native_acceptance"] is False,
        "read-only name policy scope differs",
    )
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    baseline.verify(ROOT / "Baseline/Trial.json", prior.BASE_TRIAL)
    plan = json.loads((ROOT / "Intent.json").read_bytes())
    wanted = original.prediction(plan)
    baseline.require(
        baseline.digest(ROOT / "Intent.json")
        == "0faaef5ff9bfaf0fb8e2573f758d41ffce6502c4cc93ee3a75006c956a8eb612"
        and baseline.digest(ROOT / "FrozenPrediction01.json")
        == "2ed860d27f02eafb59f8e34d672ab68d9b071d9e94d35f3b6bd72badaf78ba90"
        and wanted == json.loads((ROOT / "FrozenPrediction01.json").read_bytes()),
        "the original independent expectation changed",
    )
    authored = json.loads((ROOT / "Custody/SavedAuthor.json").read_bytes())
    baseline.require(
        authored["occurrence_ids"] == [24, 25]
        and [row["name"] for row in wanted["occurrences"]]
        == ["AuthoredAxisA-1", "AuthoredAxisB-2"]
        and authored["parent_path"] == job["native_sources"]["parent"]["guest"]
        and authored["child_path"] == job["native_sources"]["child"]["guest"],
        "the same native source paths, IDs or desired names changed",
    )
    for role, native in sources(job).items():
        baseline.checked(native, job["native_sources"][role]["sha256"])
        baseline.checked(
            ROOT / "Snapshots" / native.name,
            job["native_sources"][role]["sha256"],
        )
    return job, plan, wanted, authored


def observe(author, controller, job, wanted, authored):
    paths = sources(job)
    parent, child = paths["parent"], paths["child"]
    model, errors, warnings = author.rec.call(
        "read-only open exact same custom-name source under false setting",
        controller.open,
        str(parent),
        2,
        read_only=True,
    )
    author.rec.data["read_only_open"] = {
        "errors": errors,
        "warnings": warnings,
        "document_returned": model is not None,
        "read_only_requested": True,
    }
    author.rec.flush()
    baseline.require(
        model is not None
        and errors == warnings == 0
        and baseline.same_file(author.get(model, "GetPathName"), parent),
        "same-file false-setting open failed, warned or selected another file",
    )
    first, _ = original.capture_state(
        author, model, child, wanted, authored["occurrence_ids"]
    )
    author.rec.data["initial_read_only_state"] = first
    author.rec.flush()
    baseline.require(
        bool(author.get(model, "ForceRebuild3", False)),
        "same-file false-setting native rebuild failed",
    )
    rebuilt, _ = original.capture_state(
        author, model, child, wanted, authored["occurrence_ids"]
    )
    author.rec.data["rebuilt_read_only_state"] = rebuilt
    author.rec.flush()
    baseline.require(
        baseline.signature(first)
        == baseline.signature(rebuilt)
        == baseline.signature(authored["saved_state"]),
        "read-only false-setting source lost exact saved names or semantics",
    )
    return {"initial": first, "rebuilt": rebuilt, "same_native_source": True}


def phase(path, expected, role):
    baseline.require(os.name == "nt" and role in ROLES, "root owns native phases")
    job, plan, wanted, authored = verify(path, expected)
    prior.runtime_matches(job)
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    if role.startswith("Control"):
        row = baseline.phase(
            ROOT / "Baseline/Trial.json", prior.BASE_TRIAL, "Feature", role
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
        }
        baseline.write_json(directory / "Result.json", result)
        return result
    before = json.loads((ROOT / "Inspection/ControlBefore/Result.json").read_bytes())
    baseline.require(before["passed"] is True, "healthy leading control is required")
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
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("require idle read-only name oracle", Swapp.sweep)
            controller = recorder.call("start fresh read-only name oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact read-only name oracle",
                application_identity,
                controller.app,
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "unexpected read-only name oracle",
            )
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            baseline.require(
                int(author.get(author.app, "GetDocumentCount")) == 0,
                "read-only name oracle is not cold",
            )
            lease = ReadOnlyNamePreferenceLease(
                author, directory / "Preference", expected, identity
            )
            result["captured_original_preference"] = lease.begin()
            result["read_only_open_preference"] = bool(
                author.get(author.app, "GetUserPreferenceToggle", 18)
            )
            baseline.require(
                result["read_only_open_preference"] is False,
                "false readback changed before open",
            )
            result.update(observe(author, controller, job, wanted, authored))
            result["observation_preference_after"] = bool(
                author.get(author.app, "GetUserPreferenceToggle", 18)
            )
            baseline.require(
                result["observation_preference_after"] is False,
                "observation changed the scoped setting",
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
                    result["captured_original_preference"] = lease.original
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
        and result.get("captured_original_preference") is True
        and result.get("preference_restored") is True
        and result["immutable_inputs_unchanged"]
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


def verify_recovery(path, expected):
    baseline.require(
        baseline.digest(path) == expected and path.parent.resolve() == ROOT,
        "recovery requires the exact packet identity",
    )
    job = json.loads(path.read_bytes())
    baseline.require(
        job["schema"] == "kit.sw2026.component-name-readonly-policy.v1"
        and job["original_preference_required"] is True,
        "unexpected read-only recovery method",
    )
    for relative, digest in job["files_sha256"].items():
        if relative.endswith(".py") or relative == "ApiMetadata.json":
            baseline.checked(ROOT / relative, digest)
    return job


def recover(path, expected, output):
    job = verify_recovery(path, expected)
    prior.runtime_matches(job)
    output = output.resolve()
    baseline.require(
        output.is_relative_to(ROOT) and not output.exists(),
        "recovery output must be unused within this packet",
    )
    journal = ROOT / "Inspection/ReopenFalse/Preference"
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
        "recovery requires this exact owned capture and armed true obligation",
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
        "file_saves": 0,
        "document_setter_calls": 0,
        "native_acceptance": False,
        "preference_setter_calls": 0,
    }
    controller = None
    try:
        recorder.call("require old owned process gone and oracle idle", Swapp.sweep)
        controller = recorder.call(
            "start fresh read-only preference recovery", Swapp.Sw
        )
        identity = recorder.call(
            "verify exact read-only recovery oracle",
            application_identity,
            controller.app,
        )
        baseline.require(
            identity["sha256"] == baseline.ORACLE and identity["version_matches"],
            "unexpected recovery oracle",
        )
        result["oracle_identity"] = identity
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
                "original_value": captured["original_value"],
                "actual_value": before,
                "oracle_identity": identity,
                "capture_sha256": baseline.digest(journal / "Captured.json"),
            },
        )
        if before is not True:
            result["preference_setter_calls"] += 1
            result["setter_return"] = author.get(
                author.app, "SetUserPreferenceToggle", 18, captured["original_value"]
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
    healthy = all(
        rows.get(role, {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    result = {
        "schema": "kit.sw2026.component-name-readonly-policy-result.v1",
        "passed": bool(
            healthy
            and len(identities) == len(rows) == 3
            and all(row.get("passed") is True for row in rows.values())
        ),
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "phases": rows,
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
        "command", choices=("verify", "verify-recovery", "phase", "summary", "recover")
    )
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase", choices=ROLES)
    parser.add_argument("--recovery-output", type=Path)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.trial_sha256)
        print(json.dumps({"verified": True, "native_processes_started": 0}))
        return 0
    if args.command == "verify-recovery":
        verify_recovery(path, args.trial_sha256)
        print(
            json.dumps(
                {
                    "verified_tools_only": True,
                    "native_processes_started": 0,
                    "preference_recovery_performed": False,
                }
            )
        )
        return 0
    if args.command == "recover":
        baseline.require(
            args.recovery_output is not None, "recovery output is required"
        )
        result = recover(path, args.trial_sha256, args.recovery_output)
    elif args.command == "phase":
        result = phase(path, args.trial_sha256, args.phase)
    else:
        result = summary(path, args.trial_sha256)
    print(json.dumps({"passed": result["passed"], "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
