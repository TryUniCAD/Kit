import argparse
import json
import os
import secrets
from pathlib import Path, PureWindowsPath

from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes, windows_paths

from ChamferModel import SCHEMA as SPEC_SCHEMA, predictions, validate_spec
from ChamferPacket import FILES, create_packet, valid_hash, verify, write_new
from RunChamferSources import PHASES


def pin_record(path, pin):
    require(path.is_file() and not path.is_symlink() and valid_hash(pin) and digest(path) == pin, "source lock digest differs")
    return json.loads(path.read_bytes())


def passed_source_lock(lock, job, pin):
    require(lock["schema"] == "kit.sw2026.edge-chamfer-source-lock.v1" and lock["job_sha256"] == pin
            and all(lock[field] == job[field] for field in ("cohort", "source_revision", "source_tree"))
            and lock["spec_sha256"] == job["files"]["Spec.json"]["sha256"]
            and lock["prediction_sha256"] == job["files"]["Predictions.json"]["sha256"]
            and (lock["oracle_build"], lock["oracle_sha256"], lock["control_sha256"]) == (BUILD, ORACLE, CONTROL)
            and lock["passed"] and lock["inputs_unchanged"] and lock["idle_after"] and valid_hash(lock["api_sha256"])
            and lock["fresh_processes"] == lock["distinct_processes"] == 8 and lock["writer_output_count"] == 0
            and lock["heldout_writer_acceptance"] is False and len(lock["sources"]) == 2
            and all(lock["controls"][kind]["passed"] for kind in ("before", "after")),
            "prior lock did not bind two complete native lifecycles with healthy controls")
    for source in lock["sources"]:
        require(source["passed"] and source["snapshots"] == 4
                and [row["phase"] for row in source["phases"]] == list(PHASES)
                and all(row["passed"] and valid_hash(row["receipt_sha256"]) for row in source["phases"])
                and valid_hash(source["original_sha256"]) and valid_hash(source["edited_sha256"]),
                "source lifecycle or immutable digest is incomplete")


def private_spec():
    require(os.name == "nt", "protected operands are generated only on the guest")
    random = secrets.SystemRandom()

    def val(low, high):
        return random.randint(low, high) / 16

    names = ["Chamfer" + secrets.token_hex(6) for _ in range(2)]
    cases = [{"name": names[0], "center_mm": [val(-441, -359), val(252, 329)],
              "size_mm": [val(982, 1045), val(683, 739), val(525, 584)], "edge_axis": "y",
              "corner": {"x": "min", "z": "max"}, "distance_mm": val(97, 104), "angle_deg": val(513, 532),
              "edit": {"distance_mm": val(111, 119)}},
             {"name": names[1], "center_mm": [val(608, 679), val(-181, -100)],
              "size_mm": [val(1141, 1259), val(743, 793), val(603, 659)], "edge_axis": "z",
              "corner": {"x": "min", "y": "max"}, "distance_mm": val(35, 46), "angle_deg": val(861, 878),
              "edit": {"angle_deg": val(375, 408)}}]
    return {"schema": SPEC_SCHEMA, "cohort": "heldout", "cases": cases}


def prepare(method, method_pin, disclosed_pin, root):
    job, _, _ = verify(method, method_pin)
    original = Path(job["guest_capture"]) / "SourceLock.json"
    passed_source_lock(pin_record(original, disclosed_pin), job, method_pin)
    require(method.parent.resolve() == Path(job["guest_packet"]).resolve(), "private method must run from the verified Windows packet")
    root = root.resolve()
    packet, capture = root / "Packet", root / "Capture"
    require(root.drive.casefold() == "c:" and not root.exists()
            and not method.resolve().is_relative_to(root)
            and not root.is_relative_to(Path(job["guest_packet"]).parent.resolve()), "protected root is unbound or occupied")
    windows_paths(str(packet), str(capture), job["guest_checkout"])
    data = {name: (method.parent / name).read_bytes() for name in FILES - {"Spec.json", "Predictions.json"}}
    spec = private_spec()
    data["Spec.json"] = job_bytes(spec)
    data["Predictions.json"] = job_bytes(predictions(validate_spec(spec)))
    hidden = job | {"cohort": "heldout", "guest_packet": str(packet), "guest_capture": str(capture),
                    "method_job_sha256": method_pin, "disclosed_lock_sha256": disclosed_pin}
    pin = create_packet(packet, hidden, data)
    freeze = {"job_sha256": pin, "spec_sha256": hidden["files"]["Spec.json"]["sha256"],
              "prediction_sha256": hidden["files"]["Predictions.json"]["sha256"], "method_job_sha256": method_pin,
              "disclosed_lock_sha256": disclosed_pin, "source_revision": hidden["source_revision"],
              "slots": 2, "native_processes": 0}
    write_new(root / "PrivateFreeze.json", freeze)
    return freeze


def redact(root, pin, lock_pin, output):
    job, _, _ = verify(root / "Packet" / "SourceJob.json", pin, private=True)
    require(job["cohort"] == "heldout" and Path(job["guest_capture"]).resolve() == (root / "Capture").resolve(),
            "private capture does not bind the exact prepared job")
    share = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
    require(output.is_absolute() and output.parent.is_dir() and not output.exists()
            and PureWindowsPath(output.resolve()).is_relative_to(share),
            "redacted evidence requires a new managed share output")
    lock = pin_record(root / "Capture" / "SourceLock.json", lock_pin)
    passed_source_lock(lock, job, pin)
    result = {"schema": "kit.sw2026.edge-chamfer-prewriter-lock.v1", "source_lock_sha256": lock_pin,
              "source_job_sha256": pin, "source_revision": job["source_revision"], "source_tree": job["source_tree"],
              "method_job_sha256": job["method_job_sha256"], "disclosed_lock_sha256": job["disclosed_lock_sha256"],
              "spec_sha256": lock["spec_sha256"], "prediction_sha256": lock["prediction_sha256"],
              "registered_api_sha256": lock["api_sha256"], "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "distinct_native_processes": 8, "writer_output_count": 0, "heldout_writer_acceptance": False,
              "controls": {key: lock["controls"][key]["receipt_sha256"] for key in ("before", "after")},
              "slots": [{"slot": f"Slot{row['slot'] + 1:02d}", "original_sha256": row["original_sha256"],
                         "edited_sha256": row["edited_sha256"],
                         "phase_receipt_sha256": [phase["receipt_sha256"] for phase in row["phases"]]}
                        for row in lock["sources"]]}
    write_new(output, result)
    return {"redacted_lock_sha256": digest(output), "source_lock_sha256": lock_pin, "slots": 2, "native_processes": 0}


def main():
    require(os.name == "nt", "private source authority is guest-only")
    parser = argparse.ArgumentParser(description="Prepare and attest separate private source custody in the root-owned guest")
    mode = parser.add_subparsers(dest="mode", required=True)
    freeze = mode.add_parser("prepare")
    freeze.add_argument("--method", type=Path, required=True)
    freeze.add_argument("--method-pin", required=True)
    freeze.add_argument("--disclosed-lock-pin", required=True)
    freeze.add_argument("--private-root", type=Path, required=True)
    public = mode.add_parser("redact")
    public.add_argument("--private-root", type=Path, required=True)
    public.add_argument("--job-pin", required=True)
    public.add_argument("--lock-pin", required=True)
    public.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.private_root
    require(root.is_absolute() and root.drive.casefold() == "c:" and ".." not in root.parts, "protected custody is fixed on guest C:")
    if args.mode == "prepare":
        receipt = prepare(args.method, args.method_pin, args.disclosed_lock_pin, root)
    else:
        receipt = redact(root, args.job_pin, args.lock_pin, args.output)
    print(json.dumps(receipt, allow_nan=False))


if __name__ == "__main__":
    main()
