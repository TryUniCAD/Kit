from argparse import ArgumentParser
from pathlib import Path
from time import time
import json
import os
import sys


HERE = Path(__file__).resolve()
PACKET = "TwoStockSaveContrast01"
SCHEMA = "kit.sw2026.disclosed-two-stock-save-contrast.v1"
GENERATED_NAME = "GeneratedTwoStockGraph01.SLDPRT"
GENERATED_SHA = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
PHASES = ("before", "unchanged", "selected", "reopen", "after", "summary")
PREVIOUS_TOOLS = ("ProbeThroughMultiStock01.py", "ProbeThroughAutoScope01.py")
SELECTED_DEPTH = 0.018
SAVE_NAMES = {"Unchanged": "RebuiltUnchanged.SLDPRT", "Selected": "SelectedDepthEdited.SLDPRT"}


def probes():
    sys.path.insert(0, str(HERE.parent if os.name == "nt" else HERE.parent.parent))
    import ProbeThroughMultiStock01 as stock
    import ProbeThroughAutoScope01 as control

    return stock, control


def prepare(stock, control):
    stock.need(os.name != "nt", "freeze the disclosed contrast on macOS")
    source = stock.SHARED / "GeneratedTwoStockGraph01" / GENERATED_NAME
    stock.checked(source, GENERATED_SHA)
    control.disclosed(stock.SHARED / stock.DISCLOSED)
    folder = stock.SHARED / PACKET
    folder.mkdir(mode=0o700, exist_ok=False)
    pins = {}
    for source in (HERE, *(HERE.parent.parent / name for name in PREVIOUS_TOOLS)):
        content = source.read_bytes()
        with (folder / source.name).open("xb") as handle:
            handle.write(content)
        pins[source.name] = stock.digest(content)
    plan = {
        "schema": SCHEMA, "oracle_build": stock.BUILD, "oracle_sha256": stock.ORACLE,
        "generated_sha256": GENERATED_SHA, "selected_depth_m": SELECTED_DEPTH,
        "tools_sha256": pins, "native_trial_sha256": stock.TRIAL,
        "held_out_sources_read": 0,
    }
    return {"plan_sha256": stock.publish(folder / "Plan.json", plan), **plan}


def selected_predictions(stock):
    lo, hi = stock.DESIGN["stationary_m"]
    stock.DESIGN = {
        **stock.DESIGN, "stationary_m": [lo, [hi[0], hi[1], SELECTED_DEPTH]]
    }
    return stock.predictions()


def observe(stock, folder, phase):
    import Swapp
    from AuthorCurves import Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor

    stage = folder / phase
    stage.mkdir(exist_ok=False)
    record = Recorder(stage / "Record.json", {"schema": SCHEMA, "phase": phase})
    original = folder.parent / GENERATED_NAME
    stock.checked(original, GENERATED_SHA)
    if phase == "Reopen":
        prior = stock.prior_phase(folder, "Selected")
        stock.need(prior["passed"], "native reopen requires a successful selected-stock save")
        path, pin = folder / SAVE_NAMES["Selected"], prior["result"]["saved_sha256"]
    else:
        path, pin = original, GENERATED_SHA
    stock.checked(path, pin)
    result = {"passed": False, "input_sha256": pin}
    controller = observer = None
    with AssemblyLoadMonitor() as monitor:
        try:
            record.call("verify the native oracle is idle", Swapp.sweep)
            controller = record.call("start SOLIDWORKS", Swapp.Sw)
            identity = record.call("verify installed executable", application_identity, controller.app)
            stock.need(identity["version_matches"] and identity["file_version"] == stock.BUILD
                       and identity["sha256"] == stock.ORACLE, "native oracle identity differs")
            result["native_identity"] = identity
            observer = ThroughAllAuthor(controller.app, record, Swapp)
            model, errors, warnings = record.call(
                "open original or selected derivative", controller.open, path, read_only=phase == "Reopen"
            )
            observer.model = model
            result["open"] = [model is not None, errors, warnings]
            stock.need(result["open"] == [True, 0, 0]
                       and Path(observer.get(model, "GetPathName")).samefile(path),
                       "native open did not accept the exact path")
            predicted = selected_predictions(stock) if phase == "Reopen" else stock.predictions()
            result["snapshot"] = stock.snapshot(observer, phase, False, predicted, rebuild=True)
            if phase == "Selected":
                dimension, _ = stock.parameter(observer, stock.STEADY, 0.012)
                status = observer.get(dimension, "SetSystemValue3", SELECTED_DEPTH, 1, observer.sw.nothing())
                stock.need(int(status) == 0, "independent selected stock depth edit failed")
                result["edited"] = stock.snapshot(observer, "selected D1", False, selected_predictions(stock), rebuild=True)
                stock.need(result["snapshot"]["tree"] == result["edited"]["tree"]
                           and result["snapshot"]["profiles"] == result["edited"]["profiles"],
                           "independent selected stock depth edit changed its feature graph")
            if phase != "Reopen":
                target = folder / SAVE_NAMES[phase]
                stock.need(not target.exists(), "native contrast destination exists")
                result["save"] = list(record.call("save intended derivative", controller.save_as, model, target))
                stock.need(result["save"] == [True, 0, 0] and target.is_file()
                           and Path(observer.get(model, "GetPathName")).samefile(target),
                           "native contrast save warned or used another path")
                result["saved_sha256"] = stock.digest(target.read_bytes())
            result["passed"] = True
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and observer.model is not None:
                        record.call("close owned native model", controller.close_doc, observer.model)
                except Exception as error:
                    record.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    try:
        stock.checked(original, GENERATED_SHA)
        stock.checked(path, pin)
    except ValueError as error:
        record.failure(error)
    result["dialogs"] = monitor.log
    result["passed"] = bool(result["passed"] and record.data["first_failure"] is None
                            and not result.get("controller_diagnostics") and not result["dialogs"])
    record.data.update(result=result, passed=result["passed"], finished_at=time())
    record.flush()
    return {"phase": phase, "passed": result["passed"], "record_sha256": stock.digest(record.path.read_bytes()),
            "first_failure": record.data["first_failure"]}


def summary(stock, folder, pin):
    labels = ("Before", "Unchanged", "Selected", "Reopen", "After")
    records = {
        phase: stock.prior_phase(folder, phase)
        for phase in labels if (folder / phase / "Record.json").is_file()
    }
    stock.need(
        records.get("Before", {}).get("passed") and records.get("After", {}).get("passed"),
        "native contrast controls did not pass",
    )
    saves = {}
    for phase, name in SAVE_NAMES.items():
        record = records.get(phase)
        if record is not None and record["passed"]:
            digest = record["result"]["saved_sha256"]
            content = stock.checked(folder / name, digest)
            with HERE.with_name(name).open("xb") as handle:
                handle.write(content)
            saves[phase] = {"sha256": digest, "bytes": len(content), "name": name}
    result = {
        "schema": SCHEMA, "plan_sha256": pin, "generated_sha256": GENERATED_SHA,
        "oracle_build": stock.BUILD, "oracle_sha256": stock.ORACLE, "held_out_sources_read": 0,
        "records": {
            phase: {
                "sha256": stock.digest((folder / phase / "Record.json").read_bytes()),
                "passed": row["passed"], "numeric_checks": len(row["checks"]), "first_failure": row["first_failure"],
            }
            for phase, row in records.items()
        },
        "derivatives": saves,
    }
    stock.publish(folder / "Summary.json", result)
    return result


def run_native(stock, control, phase, pin):
    stock.need(os.name == "nt" and HERE.parent.name == PACKET and pin,
               "native contrast requires the frozen Windows packet")
    plan = json.loads(stock.checked(HERE.with_name("Plan.json"), pin))
    stock.need(plan["schema"] == SCHEMA and plan["generated_sha256"] == GENERATED_SHA
               and plan["selected_depth_m"] == SELECTED_DEPTH, "native contrast plan differs")
    for name in (HERE.name, *PREVIOUS_TOOLS):
        stock.checked(HERE.with_name(name), plan["tools_sha256"][name])
    trial_root = HERE.parent.with_name(stock.DISCLOSED)
    trial = control.disclosed(trial_root)
    sys.path.insert(0, str(trial_root / "Tools"))
    folder = Path("C:/KitSdkCandidates") / PACKET
    if phase == "before":
        folder.mkdir(exist_ok=False)
    stock.need(folder.is_dir() and not folder.is_symlink(), "native contrast directory is unavailable")
    if phase in ("before", "after"):
        return control.measure(folder, phase.capitalize(), trial_root, trial)
    stock.need(stock.prior_phase(folder, "Before")["passed"], "leading native control failed")
    return summary(stock, folder, pin) if phase == "summary" else observe(stock, folder, phase.capitalize())


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("phase", choices=("prepare", *PHASES))
    parser.add_argument("--pin")
    options = parser.parse_args()
    stock, control = probes()
    result = prepare(stock, control) if options.phase == "prepare" else run_native(stock, control, options.phase, options.pin)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
