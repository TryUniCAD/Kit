from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import sys
from traceback import print_exc
from types import ModuleType


HERE = Path(__file__).resolve()
JOB = "8bf479a956ad974f4e57b16c3b57dd2fe4eaba7958f57e58134e3fbf857fa060"
BUILD = "159796015dbeb276c5d871c9741c979bb1916f329a72eb7bbbf2ad7841e552ba"
INITIAL = "ada28820720682d301d23cf003f6032fd9ecb73a7abf041080841ffce3e5e58d"
COMPARATOR = "8619d9197153e791e8fc9db0d001a87f5c828d13505977bdedfa60296539164f"
METHOD_REVISION = "d803fe68e05c7e0aec74ddb998e2739c7eda3e9b"
RESEARCH = Path("re/tooling/sw2026/imported_body_source")
LOG_ROOT = Path(r"C:\KitSdkSealedBox03Recheck01")
LANES = ("Original", "Candidate", "FreshReopen")
STATES = ("cold", "rebuilt")
MASS_FAILURE = "native mass properties differ at six significant figures"


def require(condition, label):
    if not condition:
        raise ValueError(label)


def read(path, identity):
    require(path.is_file() and not path.is_symlink(), "expected locked regular file")
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == identity, "locked file checksum differs")
    return payload


def load(name, path, identity):
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(read(path, identity), str(path), "exec"), vars(module))
    return module


def offline(event, _arguments):
    require(event not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "ctypes.dlopen")
            and not event.startswith("socket."), "comparison attempted an external runtime")


def locked_job(job_path):
    manifest = json.loads(read(job_path, JOB))
    packet = job_path.parent.resolve()
    runner = RESEARCH / "RunSealedPublicBox.py"
    module = load("RunSealedPublicBox", packet / "Kit" / runner, manifest["file_inventory"][runner.as_posix()])
    packet, job, lock, seed, root = module.verified_job(job_path, JOB)
    require(job["method_revision"] == METHOD_REVISION and root == Path(r"C:\KitSdkSealedBox03"),
            "wrong prior native packet")
    return packet, job, lock, seed, root


def process_identity(record):
    from RunImportedBodySources import oracle_identity

    result = oracle_identity(record["oracle_identity"])
    require(result["executable"].casefold() == "sldworks.exe"
            and result["file_version_words"] == result["expected_version"] == [34, 5, 2, 604]
            and type(result["bytes"]) is int and result["bytes"] > 0, "incomplete native executable receipt")
    return result["process_id"], result["process_creation_filetime"], result["bytes"]


def bind_control(root, label, summary, target, seed):
    record = json.loads(read(root / label / "Record.json", summary["record_sha256"]))
    require(summary["passed"] is True and summary["numeric_checks"] == 0
            and Path(record["path"]) == target and record["sha256"] == sha256(seed).hexdigest()
            and record["opened"] and record["rebuilt"] and record["bodies"] > 0
            and record["open_errors"] == record["open_warnings"] == record["whats_wrong"] == 0
            and not (record.get("dialogs") or record.get("exception") or record.get("controller_diagnostics")),
            "prior control lost its verified native path or health")
    return process_identity(record)


def bind_phase(directory, label, receipt, source, read_only):
    record = json.loads(read(directory / (label + ".json"), receipt["record_sha256"]))
    result = record["result"]
    require(record["schema"] == "kit-sw2026-curve-source-phase/1" and record["job"]["case"] == label
            and record["passed"] is result["passed"] is receipt["passed"] is True
            and result["numeric_checks"] == receipt["numeric_checks"] == len(record["checks"]) == 58
            and all(check["passed"] is True for check in record["checks"])
            and not (record["first_failure"] or record["cleanup_errors"] or result["first_failure"]
                     or result["controller_diagnostics"] or result["dialogs"])
            and result["open"] == {"returned_document": True, "error": 0, "warning": 0}
            and Path(result["input_path"]) == source and result["read_only"] is read_only,
            "prior native phase lost its executed input or diagnostic binding")
    return result, process_identity(result)


def bind_case(root, slot, lock, proof, initial, method):
    row = method.public_build_row(proof["cases"][slot], lock, slot)
    require(all(initial[key] == value for key, value in row.items()) and initial["candidate_sdk_readback"] is True
            and set(initial["phases"]) == set(LANES), "prior native case differs from its exact generated publication")
    directory = root / "Native" / slot
    source = method.source_path(slot)
    target = method.candidate_path(root, slot)
    saved = directory / "NativeSave.SLDPRT"
    original, source_pid = bind_phase(directory, "Original", initial["phases"]["Original"], source, True)
    candidate, candidate_pid = bind_phase(directory, "Candidate", initial["phases"]["Candidate"], target, False)
    reopened, saved_pid = bind_phase(directory, "FreshReopen", initial["phases"]["FreshReopen"], saved, True)
    require(candidate["save"] == [True, 0, 0] and Path(candidate["saved_path"]) == saved
            and ("saved_sha256" not in initial or initial["saved_sha256"] == candidate["saved_sha256"]),
            "prior native save lost its exact freshness binding")
    payload = read(target, row["candidate"]["sha256"])
    require(len(payload) == row["candidate"]["bytes"], "generated file extent changed")
    saved_bytes = read(saved, candidate["saved_sha256"])
    return row, (original, candidate, reopened), (source_pid, candidate_pid, saved_pid), payload, saved_bytes


def compare_pair(slot, lock, row, observations, old, method):
    document, projection = method.project_source(slot, lock)
    require(method.neutral_sha(document) == row["neutral_sha256"], "locked source no longer projects to the staged neutral model")
    original, candidate, reopened = observations
    baseline = candidate["cold"]
    comparisons = []
    for state in STATES:
        for lane, label in zip(observations, (projection.feature_name, method.FEATURE, method.FEATURE), strict=True):
            snapshot = lane[state]
            require(snapshot["feature"] == label and snapshot["feature_faces"] == 6
                    and snapshot["configuration"] == projection.configuration_name
                    and snapshot["configurations"] == [projection.configuration_name]
                    and snapshot["application_state"]["needs_rebuild"] == 0,
                    "prior native configuration, feature ownership or rebuild differs")
        for lane in (candidate, reopened):
            snapshot = lane[state]
            require(all(snapshot[key] == baseline[key] for key in
                        ("feature_id", "persistent_reference", "tree_signature")),
                    "prior candidate identity changed across its native lifecycle")
            comparisons.append((original[state]["shape"], snapshot["shape"]))
    old_passed = True
    for reference, snapshot in comparisons:
        try:
            old.compare_shape(reference, snapshot)
        except ValueError as error:
            require(str(error) == MASS_FAILURE, "original comparator records a non-mass failure")
            old_passed = False
    require(old_passed == (slot == "Slot01"), "original comparator did not reproduce the baseline split")
    return projection, comparisons, old_passed


def recheck(args):
    packet, job, lock, seed, root = locked_job(args.job)
    public = args.output.resolve()
    require(args.output.is_absolute() and public == args.output and not public.exists()
            and not public.is_relative_to(packet) and not public.is_relative_to(root)
            and not public.is_relative_to(LOG_ROOT), "use a new sanitized receipt outside both private packet roots")
    initial_path, build_path = packet / "Result.json", root / "Build.json"
    initial = json.loads(read(initial_path, INITIAL))
    proof = json.loads(read(build_path, BUILD))
    old = import_module("CheckSealedPublicBox")
    method = load("CorrectedSealedPublicBox", HERE.with_name("CheckSealedPublicBox.py"), COMPARATOR)
    slots = method.SLOTS
    require(initial["schema"] == method.SCHEMA + "-native.v1" and proof["schema"] == method.SCHEMA + "-build.v1"
            and initial["job_sha256"] == proof["job_sha256"] == JOB and initial["build_sha256"] == BUILD
            and initial["source_lock_sha256"] == proof["source_lock_sha256"] == method.RAW_LOCK_SHA
            and initial["source_receipt_sha256"] == job["source_receipt_sha256"] == method.LOCK_SHA
            and initial["specifications_sha256"] == proof["specifications_sha256"] == lock["specifications_sha256"]
            and initial["sdk_revision"] == job["sdk_revision"] and initial["method_revision"] == METHOD_REVISION
            and initial["oracle_version"] == method.VERSION and initial["oracle_sha256"] == method.ORACLE
            and initial["passed"] is False and initial["controls_healthy"] is True
            and initial["originals_and_specifications_unchanged"] is True
            and initial["native_processes"] == 8 and proof["native_processes_started"] == 0
            and initial["complete_paired_regressions"] == 0 and initial["prior_locked_cases"] == len(slots)
            and tuple(initial["cases"]) == tuple(proof["cases"]) == slots, "third-packet native/build lock differs")
    for flag in ("new_independent_cases", "original_fcstd_conversions", "whole_source_conversions",
                 "original_specs_and_payloads_shared"):
        require(initial[flag] == 0, "unexpected prior scope credit")
    require(initial["cases"]["Slot01"]["passed"] is True and initial["cases"]["Slot01"]["native_saved_sdk_readback"] is True
            and initial["cases"]["Slot02"]["passed"] is False
            and initial["cases"]["Slot02"]["error_type"] == "ValueError", "prior split differs")
    control_root = root / "Native"
    control = control_root / "Control.SLDPRT"
    require(read(control, job["control_sha256"]) == seed, "exact bracket control changed")
    identities = [bind_control(control_root, "ControlBefore", initial["controls"]["ControlBefore"], control, seed)]
    cases = {}
    method.warm()
    for slot in slots:
        before = initial["cases"][slot]
        row, observations, processes, payload, saved = bind_case(root, slot, lock, proof, before, method)
        identities.extend(processes)
        projection, comparisons, old_passed = compare_pair(slot, lock, row, observations, old, method)
        result = cases[slot] = row | {"saved_sha256": observations[1]["saved_sha256"],
                                      "native_phases": before["phases"], "old_mass_comparison_passed": old_passed}
        for name, action in (
            ("candidate_sdk_readback", lambda: method.readback(payload, projection)),
            ("native_saved_sdk_readback", lambda: method.readback(saved, projection, saved=True)),
            ("six_significant_figures", lambda: check_comparisons(method, comparisons)),
        ):
            try:
                action()
                result[name] = True
            except Exception:
                print_exc()
                result[name] = False
        result["passed"] = all(result[key] for key in (
            "candidate_sdk_readback", "native_saved_sdk_readback", "six_significant_figures",
        ))
    identities.append(bind_control(control_root, "ControlAfter", initial["controls"]["ControlAfter"], control, seed))
    chronology = [time for _, time, _ in identities]
    require(len(set(identities)) == len(set(chronology)) == len(identities) == 8
            and chronology == sorted(chronology) and len({length for _, _, length in identities}) == 1,
            "prior phases do not bind eight bracketed fresh processes of the exact executable")
    method.check_originals(lock)
    read(initial_path, INITIAL)
    read(build_path, BUILD)
    passed = all(row["passed"] for row in cases.values())
    report = {"schema": method.SCHEMA + "-readjudication.v1", "passed": passed,
              "prior_result_sha256": INITIAL, "prior_result_passed": False, "job_sha256": JOB, "build_sha256": BUILD,
              "method_sha256": args.method_sha256, "comparator_sha256": COMPARATOR, "sdk_revision": job["sdk_revision"],
              "prior_method_revision": METHOD_REVISION, "oracle_sha256": method.ORACLE, "oracle_version": method.VERSION,
              "source_receipt_sha256": method.LOCK_SHA, "source_lock_sha256": method.RAW_LOCK_SHA,
              "specifications_sha256": lock["specifications_sha256"], "prior_native_processes": 8,
              "native_processes_started": 0, "controls_healthy": True, "controls": initial["controls"],
              "originals_and_specifications_unchanged": True, "cases": cases, "prior_locked_cases": len(slots),
              "new_independent_cases": 0, "original_fcstd_conversions": 0, "whole_source_conversions": 0,
              "original_specs_and_payloads_shared": 0, "source_omissions": method.SOURCE_OMISSIONS,
              "complete_paired_regressions": len(slots) if passed else 0}
    return {"passed": passed, "result_sha256": method.publish(public, report)}


def check_comparisons(method, comparisons):
    for reference, snapshot in comparisons:
        method.compare_shape(reference, snapshot)


def main():
    parser = ArgumentParser(description="Recheck the locked third rectangular packet without CAD")
    parser.add_argument("job", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--method-sha256", required=True)
    args = parser.parse_args()
    require(os.name == "nt" and sys.dont_write_bytecode, "use the owned Windows guest with -B")
    read(HERE, args.method_sha256)
    LOG_ROOT.mkdir()
    with (LOG_ROOT / "Recheck.log").open("x", encoding="utf-8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            try:
                sys.addaudithook(offline)
                result = recheck(args)
            except Exception as error:
                print_exc()
                result = {"passed": False, "error_type": type(error).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
