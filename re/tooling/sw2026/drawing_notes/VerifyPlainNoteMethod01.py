from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path, expected):
    raw = path.read_bytes()
    require(len(raw) <= 2_000_000 and sha256(raw).hexdigest() == expected,
            "frozen metadata identity or size differs")
    return loads(raw)


def main():
    parser = ArgumentParser()
    parser.add_argument("--method", type=Path, required=True)
    parser.add_argument("--method-sha256", required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    method = read_json(args.method, args.method_sha256)
    require(method["schema"] == "kit.sw2026.plain-note-preunseal-method.v1"
            and method["scope"]["private_payloads_read"] == 0
            and method["scope"]["native_calls"] == 0,
            "unexpected method or exposure declaration")
    require(sha256(Path(__file__).read_bytes()).hexdigest() == method["metadata_verifier_sha256"],
            "metadata verifier differs from the frozen method")
    lock = read_json(args.source_lock, method["public_source_lock"]["sha256"])
    require(lock["schema"] == "kit.sw2026.drawing-plain-note-source.v1"
            and lock["passed"] is True
            and lock["private_source_values_disclosed"] is False
            and lock["writer_generated_cases"] == 0
            and lock["distinct_passing_processes"] == 14
            and lock["failure"] == []
            and lock["prewriter_revision"] == method["public_source_lock"]["prewriter_revision"],
            "public prewriter source lock is not the qualified metadata record")
    actual = {name: row for name, row in lock["source_cases"].items() if row["private"]}
    require(set(actual) == set(method["sealed_slots"]) == {"Slot01", "Slot02"},
            "sealed slot set differs")
    for name, wanted in method["sealed_slots"].items():
        require({key: actual[name][key] for key in wanted} == wanted,
                "sealed source hashes changed")
    roles = method["native_roles"]
    require(len(roles) == len(set(roles)) == 13
            and roles[:2] == ["ControlBefore", "NativeNoteSourceControl"]
            and roles[-1] == "ControlAfter", "native role schedule differs")
    require(method["writer_binding"]["status"] == "pending_root_sdk_freeze"
            and method["writer_binding"]["private_source_exposure_allowed"] is False
            and method["qualification"]["heldout_passed"] is False
            and method["qualification"]["public_writer_qualified"] is False,
            "unexecuted method implies a qualification or exposure permit")
    report = {
        "schema": "kit.sw2026.plain-note-preunseal-metadata-result.v1",
        "metadata_verified": True,
        "method_sha256": args.method_sha256,
        "source_lock_sha256": method["public_source_lock"]["sha256"],
        "sealed_slots": sorted(actual),
        "planned_native_phases": len(roles),
        "writer_closure_bound": False,
        "source_exposure_ready": False,
        "native_processes": 0,
        "private_payloads_read": 0,
        "cad_files_opened": 0,
        "heldout_passed": False,
        "public_writer_qualified": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(dumps({key: report[key] for key in (
        "metadata_verified", "planned_native_phases", "source_exposure_ready",
        "native_processes", "private_payloads_read",
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
