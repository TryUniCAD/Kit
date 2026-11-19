from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path

from InspectFresh import healthy, inspect
from OracleIdentity import application_identity
import Swapp


APP_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
DEPTH_PARAMETER = "D1@Boss-Extrude1"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(success, reason):
    if not success:
        raise ValueError(reason)


def snapshot(model):
    extension = model.Extension
    return {"needs_rebuild": int(Swapp.cv(extension, "NeedsRebuild2")),
            "save_flag": bool(Swapp.cv(model, "GetSaveFlag")), "bodies": Swapp.bodies(model),
            "whats_wrong": Swapp.rebuild_errors(model), "mass": Swapp.mass(model)}


def check_shape(observed, expected):
    require(observed["bodies"] == 1 and observed["whats_wrong"] == 0, "expected clean ordinary prism")
    actual = observed["mass"]
    for left, right in zip((actual["volume"], actual["area"], *actual["com"]),
                           (expected["volume"], expected["area"], *expected["com"]), strict=True):
        require(isclose(left, right, rel_tol=5e-7, abs_tol=1e-12), "ordinary prism geometry differs")


def phase(source, expected_sha, expected, *, edited=None, row, checkpoint):
    path = Path(source)
    require(digest(path) == expected_sha, "native phase input changed")
    model = None
    session = None
    row.update(path=path.name, input_sha256=expected_sha, stage="fresh COM launch", passed=False)
    checkpoint()
    try:
        Swapp.sweep()
        session = Swapp.Sw()
        identity = application_identity(session.app)
        row["oracle"] = identity
        require(identity["version_matches"] and identity["sha256"] == APP_SHA256, "wrong native process build")
        row["stage"] = "open"
        checkpoint()
        model, errors, warnings = session.open(path)
        row["open"] = {"opened": model is not None, "errors": errors, "warnings": warnings}
        require(model is not None and errors == 0 and warnings in (0, 32), "native prism failed to open")
        row["before_rebuild"] = snapshot(model)
        require(bool(model.ForceRebuild3(False)), "ordinary prism rebuild failed")
        row["rebuilt"] = snapshot(model)
        check_shape(row["rebuilt"], expected)
        dimension = Swapp.invoke(model, "Parameter", DEPTH_PARAMETER)
        require(dimension is not None, "persistent depth parameter is missing")
        value = float(Swapp.cv(dimension, "SystemValue"))
        row["depth_m"] = value
        require(isclose(value, expected["depth"], rel_tol=5e-7, abs_tol=1e-12), "initial depth differs")

        if edited is not None:
            output, geometry = edited
            require(not output.exists(), "native save destination already exists")
            row["stage"] = "parameter edit"
            checkpoint()
            status = int(Swapp.cv(dimension, "SetSystemValue3", geometry["depth"], 1, Swapp.nothing()))
            row["setter_status"] = status
            require(status == 0 and bool(model.ForceRebuild3(False)), "depth edit did not rebuild")
            row["edited"] = snapshot(model)
            check_shape(row["edited"], geometry)
            require(isclose(float(Swapp.cv(dimension, "SystemValue")), geometry["depth"],
                            rel_tol=5e-7, abs_tol=1e-12), "edited depth differs")
            row["stage"] = "save separate part"
            checkpoint()
            saved = session.save_as(model, output)
            row["save"] = {"success": saved[0], "errors": saved[1], "warnings": saved[2]}
            require(saved == (True, 0, 0) and output.is_file(), "native edited copy failed to save cleanly")
            row["saved_file"] = output.name
            row["saved_sha256"] = digest(output)
        require(digest(path) == expected_sha, "native phase modified its original input")
        row["passed"] = True
        row["stage"] = "completed"
    except Exception as error:
        row["exception"] = repr(error)
    finally:
        if session is not None:
            if model is not None:
                session.close_doc(model)
            session.close()
            row["controller_diagnostics"] = session.diagnostics
            if session.diagnostics:
                row["passed"] = False
        checkpoint()


def main():
    parser = ArgumentParser()
    parser.add_argument("job", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    command = loads(args.job.read_bytes())
    controls = []
    results = []
    report = {"schema": "kit.sw2026.disclosed-prism-cache-edits.v1", "controls": controls,
              "results": results, "source_job_sha256": digest(args.job),
              "heldout_inputs_read": 0, "finished": False}

    def checkpoint():
        args.receipt.write_text(dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def control():
        item = {}
        controls.append(item)
        path = Path(command["control"])
        require(digest(path) == command["control_sha256"], "native control changed")
        inspect(path, result=item, checkpoint=checkpoint)
        item["passed"] = healthy(item) and digest(path) == command["control_sha256"]
        checkpoint()

    with args.receipt.open("x", encoding="utf-8"):
        pass
    control()
    for case in command["cases"]:
        edited = None if case.get("edited") is None else Path(case["edited"])
        result = {"case": case["case"], "edit": {}, "reopen": {}}
        results.append(result)
        phase(case["input"], case["sha256"], case["initial"],
              edited=None if edited is None else (edited, case["target"]),
              row=result["edit"], checkpoint=checkpoint)
        if edited is not None and result["edit"]["passed"]:
            phase(edited, result["edit"]["saved_sha256"], case["target"],
                  row=result["reopen"], checkpoint=checkpoint)
    control()
    report["finished"] = True
    report["lifecycle_passed"] = all(row["passed"] for row in controls) and all(
        result["edit"]["passed"] and (case.get("edited") is None or result["reopen"].get("passed"))
        for result, case in zip(results, command["cases"], strict=True)
    )
    report["clean_initial_opens"] = all(
        case["edit"].get("open", {}).get("warnings") == 0 for case in results
    )
    checkpoint()
    return 0 if report["lifecycle_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
