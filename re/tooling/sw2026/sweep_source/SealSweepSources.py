import argparse
import json
import os
import sys
from pathlib import Path, PureWindowsPath

from RunSweepSources import LOCK_SCHEMA, PROCESS_COUNT, case_paths
from SweepModel import PARAMETERS, PHASES, predictions, require, validate_spec
from SweepPacket import BUILD, CONTROL, FILES, ORACLE, create_packet, digest, job_bytes, valid_hash, verify, windows_paths, write_new


def pinned_json(path, pin):
    require(valid_hash(pin) and path.is_file() and not path.is_symlink() and digest(path) == pin,
            "required exact source evidence digest differs")
    return json.loads(path.read_bytes())


def passed_lock(lock, job, pin):
    require(lock["schema"] == LOCK_SCHEMA and lock["job_sha256"] == pin
            and all(lock[key] == job[key] for key in ("cohort", "source_revision", "source_tree"))
            and (lock["oracle_build"], lock["oracle_sha256"], lock["control_sha256"]) == (BUILD, ORACLE, CONTROL)
            and lock["spec_sha256"] == job["files"]["Spec.json"]["sha256"]
            and lock["prediction_sha256"] == job["files"]["Predictions.json"]["sha256"]
            and valid_hash(lock["api_sha256"]) and lock["passed"] and lock["inputs_unchanged"] and lock["idle_after"]
            and lock["fresh_processes"] == lock["distinct_processes"] == PROCESS_COUNT
            and lock["writer_output_count"] == 0 and lock["heldout_writer_acceptance"] is False
            and [source["slot"] for source in lock["sources"]] == [0, 1]
            and all(lock["controls"][key]["passed"] and valid_hash(lock["controls"][key]["receipt_sha256"])
                    for key in ("before", "after")), "native source batch did not completely pass")
    for source in lock["sources"]:
        require(source["passed"] and source["snapshots"] == 7 and source["cold_snapshots"] == 4
                and [row["phase"] for row in source["phases"]] == list(PHASES)
                and all(row["passed"] and row["checks"] == row["checks_passed"] > 0 and valid_hash(row["receipt_sha256"])
                        for row in source["phases"])
                and set(source["artifact_sha256"]) == {"original", "section", "path"}
                and all(valid_hash(value) for value in source["artifact_sha256"].values()),
                "a source has an incomplete native owner, edit or digest")


def guest_private_path(path):
    require(path.is_absolute() and path.drive.casefold() == "c:" and ".." not in path.parts and path.resolve() == path,
            "protected sources must remain at canonical native guest C: locators")
    return path


def prepare(method, method_pin, disclosed_pin, protected_spec, spec_pin, root):
    job, declared, _ = verify(method, method_pin)
    require(method.parent.resolve() == Path(job["guest_packet"]).resolve()
            and Path(__file__).resolve().parent == method.parent / "Tool", "run from the original verified guest method")
    original = Path(job["guest_capture"]) / "SourceLock.json"
    disclosed = pinned_json(original, disclosed_pin)
    passed_lock(disclosed, job, method_pin)
    packet, capture = root / "Packet", root / "Capture"
    require(not root.exists() and not root.is_relative_to(method.parent.parent.resolve())
            and not root.is_relative_to(original.parent.resolve()) and not protected_spec.is_relative_to(root)
            and not protected_spec.is_relative_to(method.parent.parent.resolve())
            and not protected_spec.is_relative_to(original.parent.resolve()) and not protected_spec.is_symlink(),
            "protected intent and outputs require separate stationary custody")
    windows_paths(str(packet), str(capture), job["guest_checkout"])
    spec = pinned_json(protected_spec, spec_pin)
    _, cases = validate_spec(spec)
    disclosed_values = {case[key] for case in declared["cases"] for key in PARAMETERS}
    protected_values = {case[key] for case in cases for key in PARAMETERS}
    require(spec["cohort"] == "heldout" and len(protected_values) == 2 * len(PARAMETERS)
            and disclosed_values.isdisjoint(protected_values), "protected source inputs repeat coordinates from disclosed cases")
    data = {filename: (method.parent / filename).read_bytes() for filename in FILES - {"Spec.json", "Predictions.json"}}
    data["Spec.json"] = protected_spec.read_bytes()
    require(digest(protected_spec) == spec_pin and json.loads(data["Spec.json"]) == spec,
            "protected intent changed during staging")
    data["Predictions.json"] = job_bytes(predictions(spec))
    private_job = job | {"cohort": "heldout", "guest_packet": str(packet), "guest_capture": str(capture),
                         "method_job_sha256": method_pin, "disclosed_lock_sha256": disclosed_pin}
    pin = create_packet(packet, private_job, data)
    freeze = {"job_sha256": pin, "spec_sha256": spec_pin, "prediction_sha256": private_job["files"]["Predictions.json"]["sha256"],
              "method_job_sha256": method_pin, "disclosed_lock_sha256": disclosed_pin, "source_revision": job["source_revision"],
              "slots": 2, "native_processes": 0}
    write_new(root / "PrivateFreeze.json", freeze)
    return freeze


def verify_records(lock, capture, spec):
    require(digest(capture / "RegisteredApi.json") == lock["api_sha256"], "registered API evidence changed")
    for kind in ("before", "after"):
        row = lock["controls"][kind]
        record = pinned_json(capture / row["phase"] / "Record.json", row["receipt_sha256"])
        require(record["passed"] and record["sha256"] == CONTROL, "immutable control receipt differs")
    for source, case in zip(lock["sources"], spec["cases"], strict=True):
        folder, original, derivatives = case_paths(capture, source["slot"], case)
        require({key: digest(path) for key, path in ({"original": original} | derivatives).items()}
                == source["artifact_sha256"], "native files differ from their source lock")
        for row in source["phases"]:
            native = pinned_json(folder / row["phase"] / "Record.json", row["receipt_sha256"])
            require(native["passed"] and native["source_immutable"] and native["writer_output_count"] == 0
                    and native["native_sha256"] == row["artifact_sha256"], "native terminal phase differs")


def redact(root, pin, lock_pin, output):
    job, spec, _ = verify(root / "Packet" / "SourceJob.json", pin, permit_private=True)
    capture = root / "Capture"
    require(job["cohort"] == "heldout" and Path(job["guest_capture"]) == capture,
            "protected terminal capture is outside its original oracle job")
    share = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
    require(output.is_absolute() and not output.exists() and output.parent.is_dir()
            and PureWindowsPath(output.resolve()).is_relative_to(share), "use a fresh managed share path for the digest-only result")
    lock = pinned_json(capture / "SourceLock.json", lock_pin)
    passed_lock(lock, job, pin)
    verify_records(lock, capture, spec)
    result = {"schema": "kit.sw2026.standard-sweep-prewriter-lock.v1", "source_lock_sha256": lock_pin,
              "source_job_sha256": pin, "source_revision": job["source_revision"], "source_tree": job["source_tree"],
              "method_job_sha256": job["method_job_sha256"], "disclosed_lock_sha256": job["disclosed_lock_sha256"],
              "spec_sha256": lock["spec_sha256"], "prediction_sha256": lock["prediction_sha256"],
              "registered_api_sha256": lock["api_sha256"], "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "distinct_native_processes": PROCESS_COUNT, "writer_output_count": 0, "heldout_writer_acceptance": False,
              "controls": {key: lock["controls"][key]["receipt_sha256"] for key in ("before", "after")},
              "slots": [{"slot": f"Slot{source['slot'] + 1:02d}", "artifact_sha256": source["artifact_sha256"],
                         "phase_receipt_sha256": [phase["receipt_sha256"] for phase in source["phases"]]}
                        for source in lock["sources"]]}
    write_new(output, result)
    return {"redacted_lock_sha256": digest(output), "source_lock_sha256": lock_pin, "slots": 2, "native_processes": 0}


def main():
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "private source authority is guest-only CPython 3.12")
    parser = argparse.ArgumentParser(description="Prepare guest-private sweep sources and publish only their lock digests")
    modes = parser.add_subparsers(dest="mode", required=True)
    freeze = modes.add_parser("prepare")
    freeze.add_argument("--method", type=Path, required=True)
    freeze.add_argument("--method-pin", required=True)
    freeze.add_argument("--disclosed-lock-pin", required=True)
    freeze.add_argument("--protected-spec", type=Path, required=True)
    freeze.add_argument("--spec-pin", required=True)
    freeze.add_argument("--private-root", type=Path, required=True)
    publish = modes.add_parser("redact")
    publish.add_argument("--private-root", type=Path, required=True)
    publish.add_argument("--job-pin", required=True)
    publish.add_argument("--lock-pin", required=True)
    publish.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = guest_private_path(args.private_root)
    if args.mode == "prepare":
        spec = guest_private_path(args.protected_spec)
        result = prepare(args.method, args.method_pin, args.disclosed_lock_pin, spec, args.spec_pin, root)
    else:
        result = redact(root, args.job_pin, args.lock_pin, args.output)
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
