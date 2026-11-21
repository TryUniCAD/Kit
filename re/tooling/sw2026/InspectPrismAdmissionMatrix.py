from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path

from OracleIdentity import application_identity
import Swapp


EXECUTABLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def observe(app, path, *, read_only):
    model, errors, warnings = app.open(path, read_only=read_only)
    result = {"errors": errors, "warnings": warnings, "opened": model is not None}
    if model is not None:
        try:
            result["bodies"] = Swapp.bodies(model)
            result["needs_rebuild"] = int(Swapp.cv(model.Extension, "NeedsRebuild2"))
            result["save_flag"] = bool(Swapp.cv(model, "GetSaveFlag"))
            if result["bodies"] == 1:
                result["mass"] = Swapp.mass(model)
        finally:
            app.close_doc(model)
    return result


def healthy(result):
    return (
        result["errors"] == 0
        and result["warnings"] == 0
        and result["opened"]
        and result["bodies"] == 1
        and result["needs_rebuild"] == 0
    )


def phase(path, warmup, read_only):
    outcome = {"read_only": read_only, "warmup": warmup is not None, "observed": False}
    app = None
    try:
        Swapp.sweep()
        app = Swapp.Sw()
        identity = application_identity(app.app)
        outcome["oracle"] = identity
        if not identity["version_matches"] or identity["sha256"] != EXECUTABLE_SHA256:
            raise RuntimeError("unexpected SOLIDWORKS executable")
        if warmup is not None:
            outcome["warmup_observation"] = observe(app, warmup, read_only=True)
            result = outcome["warmup_observation"]
            if result["errors"] or result["warnings"] not in (0, 2) or result.get("bodies") != 1:
                raise RuntimeError("warm-up control could not restore the known healthy body")
        outcome["open"] = observe(app, path, read_only=read_only)
        outcome["observed"] = True
    except Exception as error:
        outcome["exception"] = repr(error)
    finally:
        if app is not None:
            app.close()
            outcome["controller_diagnostics"] = app.diagnostics
            if app.diagnostics:
                outcome["observed"] = False
    return outcome


def main():
    parser = ArgumentParser()
    parser.add_argument("control", type=Path)
    parser.add_argument("control_sha256")
    parser.add_argument("warmup", type=Path)
    parser.add_argument("warmup_sha256")
    parser.add_argument("part", type=Path)
    parser.add_argument("part_sha256")
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    custody = {
        args.control: args.control_sha256,
        args.warmup: args.warmup_sha256,
        args.part: args.part_sha256,
    }
    if len(custody) != 3 or any(digest(path) != expected for path, expected in custody.items()):
        raise ValueError("diagnostic input changed")
    report = {
        "schema": "kit.sw2026.disclosed-prism-admission-matrix.v1",
        "heldout_inputs_read": 0,
        "instrumented": False,
        "rebuild_calls": 0,
        "save_calls": 0,
        "inputs": {path.name: expected for path, expected in custody.items()},
        "phases": {},
        "passed": False,
    }
    with args.receipt.open("x", encoding="utf-8"):
        pass

    def record(name, path, warmup, read_only):
        result = phase(path, warmup, read_only)
        report["phases"][name] = result
        checkpoint()
        return result

    def checkpoint():
        args.receipt.write_text(dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    before = record("before", args.control, None, False)
    if before["observed"] and healthy(before["open"]):
        for boot, warmup in (("cold", None), ("warm", args.warmup)):
            for mode, read_only in (("writable", False), ("read_only", True)):
                record(boot + "_" + mode, args.part, warmup, read_only)
    after = record("after", args.control, None, False)
    report["controls_healthy"] = all(result["observed"] and healthy(result["open"]) for result in (before, after))
    report["distinct_processes"] = len({
        row["oracle"]["process_creation_filetime"]
        for row in report["phases"].values()
        if row.get("oracle")
    })
    report["input_custody"] = all(digest(path) == expected for path, expected in custody.items())
    report["passed"] = (
        report["controls_healthy"]
        and report["distinct_processes"] == 6
        and report["input_custody"]
        and all(row["observed"] for row in report["phases"].values())
    )
    checkpoint()
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
