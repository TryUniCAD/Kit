import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import InspectFresh
import Swapp
from AuthorOpenShell import CONTROL, check_geometry, check_identity, require
from OracleIdentity import application_identity

SCHEMA = "kit-sw2026-generated-open-shell-native-v1"
CALIBRATION = "84cc9032447eefd717f9fb4bc3a6c62ecf941af80aa45da861ca7bd1d456f4a1"
PARAMETER = "D1@OpenShell"
STOCK_PARAMETER = "D1@ShellStockBoss"
DIMENSIONS = (0.053, 0.041, 0.028, 0.0028, 0.00353)
EXPECTED_PATH = r"C:\KitOpenShellGenerated01\Working\OpenShellCalibration.SLDPRT"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def close_number(value, target, label):
    require(math.isclose(value, target, rel_tol=4e-7, abs_tol=1e-12), label)


def check_control(path, result, role):
    require(digest(path) == CONTROL, "independent native control hash differs")
    observed = InspectFresh.inspect(path)
    result[role] = observed
    require(InspectFresh.healthy(observed) and digest(path) == CONTROL,
            "independent shell control is unhealthy")
    check_identity(observed["oracle_identity"])


def dimension(model, name, value):
    parameter = Swapp.invoke(model, "Parameter", name)
    require(parameter is not None and not Swapp.cv(parameter, "ReadOnly")
            and Swapp.cv(parameter, "DrivenState") == 2, f"{name} is not a live driving dimension")
    close_number(Swapp.cv(parameter, "SystemValue"), value, f"{name} differs from the independent value")
    return parameter


def measure(model, edited):
    require(Swapp.invoke(model, "ForceRebuild3", False) and Swapp.rebuild_errors(model) == 0, "shell did not rebuild cleanly")
    extension = Swapp.cv(model, "ConfigurationManager")
    configuration = Swapp.cv(Swapp.cv(extension, "ActiveConfiguration"), "Name")
    require(configuration == "Default", "unexpected shell configuration")
    solids = tuple(Swapp.invoke(model, "GetBodies2", 0, False) or ())
    require(len(solids) == 1 and not Swapp.invoke(model, "GetBodies2", 1, False), "shell needs one solid and no sheets")
    actual = {"bodies": len(solids), "mass": Swapp.mass(model), "features": Swapp.features(model),
              "native_face_count": int(Swapp.cv(solids[0], "GetFaceCount")), "configuration": configuration}
    require(actual["native_face_count"] == 11, "open rectangular shell must have its eleven real faces")
    require(all(row.get("error") == 0 and row.get("warning") is False for row in actual["features"]),
            "the shell feature tree has a rebuild error or warning")
    check_geometry(actual, DIMENSIONS, edited, PARAMETER)
    dimension(model, STOCK_PARAMETER, DIMENSIONS[2])
    parameter = dimension(model, PARAMETER, DIMENSIONS[4 if edited else 3])
    return actual, parameter


def open_edit(candidate, edited, result):
    controller = None
    with Swapp.Dismisser() as watcher:
        try:
            Swapp.sweep()
            controller = Swapp.Sw()
            result["oracle_identity"] = application_identity(controller.app)
            check_identity(result["oracle_identity"])
            require(int(Swapp.cv(controller.app, "GetDocumentCount")) == 0, "native shell trial process is not fresh")
            model, errors, warnings = controller.open(candidate)
            result["open_errors"], result["open_warnings"] = errors, warnings
            require(model is not None and errors == warnings == 0, "generated shell did not open cleanly")
            require(Path(Swapp.cv(model, "GetPathName")).samefile(candidate), "native oracle opened a different part")
            result["cold_bodies"] = Swapp.bodies(model)
            require(result["cold_bodies"] == 1, "generated shell opened without exactly one native solid")
            result["before"], parameter = measure(model, False)
            result["edit_status"] = Swapp.invoke(parameter, "SetSystemValue3", DIMENSIONS[4], 1, Swapp.nothing())
            require(result["edit_status"] == 0, "generated shell rejected its actual wall driver edit")
            result["edited"], _ = measure(model, True)
            result["save_status"] = controller.save_as(model, edited)
            require(result["save_status"] == (True, 0, 0), "generated shell edit did not save cleanly")
            result["edited_sha256"] = digest(edited)
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = watcher.log
    require(not result["controller_diagnostics"] and not watcher.log, "native shell session had diagnostics")
    require(digest(candidate) == CALIBRATION, "generated shell source changed")


def validate_reopen(path, result):
    edited = result["edit"]["edited_sha256"]
    require(digest(path) == edited, "edited shell changed before reopen")
    reopen = InspectFresh.inspect(path, parameter_names=(PARAMETER, STOCK_PARAMETER))
    result["reopen"] = reopen
    check_identity(reopen["oracle_identity"])
    require(InspectFresh.healthy(reopen) and digest(path) == edited, "generated comparison shell reopened with errors")
    check_geometry(reopen, DIMENSIONS, True, PARAMETER)
    close_number(reopen["parameters"][STOCK_PARAMETER], DIMENSIONS[2], "reopened stock depth differs")
    close_number(reopen["parameters"][PARAMETER], DIMENSIONS[4], "reopened thickness differs")
    rows = [(row["name"], row["type"]) for row in reopen["features"]]
    require(rows == [(row["name"], row["type"]) for row in result["edit"]["edited"]["features"]],
            "generated shell tree differs after save and reopen")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--edited", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    require(str(args.candidate).casefold() == EXPECTED_PATH.casefold() and digest(args.candidate) == CALIBRATION,
            "generated shell must use the exact encoded locator and file")
    require(args.edited.name == args.candidate.name and not args.edited.exists()
            and not args.result.exists(), "native shell trial requires unique output paths")
    result = {"schema": SCHEMA, "passed": False, "candidate_sha256": CALIBRATION, "edit": {},
              "historical_corpus_credit": 0, "heldout_credit": 0}
    try:
        check_control(args.control, result, "control_before")
        open_edit(args.candidate, args.edited, result["edit"])
        validate_reopen(args.edited, result)
    except Exception as error:
        result["failure"] = repr(error)
    finally:
        try:
            check_control(args.control, result, "control_after")
        except Exception as error:
            result["trailing_control_failure"] = repr(error)
    phases = ("control_before", "edit", "reopen", "control_after")
    lifetimes = [result[name]["oracle_identity"]["process_creation_filetime"] for name in phases
                 if result.get(name, {}).get("oracle_identity")]
    result["passed"] = not {"failure", "trailing_control_failure"} & result.keys() and len(set(lifetimes)) == 4
    with args.result.open("x", encoding="utf-8") as file:
        json.dump(result, file, indent=2, allow_nan=False)
        file.write("\n")
    Swapp.emit({"passed": result["passed"], "candidate_sha256": CALIBRATION,
                "fresh_processes": len(set(lifetimes))})
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
