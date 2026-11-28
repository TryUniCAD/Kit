from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
from time import time
import codecs
import json
import os
import sys


HERE = Path(__file__).resolve()
PACKET = "GeneratedTwoStockGraph01"
PART = PACKET + ".SLDPRT"
SCHEMA = "kit.sw2026.disclosed-two-stock-construction.v1"
PHASES = ("before", "open", "reopen", "after", "summary")
STOCK = "ProbeThroughMultiStock01.py"
CONTROL = "ProbeThroughAutoScope01.py"


def import_probes():
    source = HERE.parent if os.name == "nt" else HERE.parent.parent
    sys.path.insert(0, str(source))
    import ProbeThroughAutoScope01 as control
    import ProbeThroughMultiStock01 as stock

    return control, stock


def generate():
    repo = HERE.parents[5]
    folder = HERE.parent
    sys.path[:0] = [str(repo / "src"), str(folder), str(folder.parent / "twostockshape")]
    from BuildTwoStockGraph import build_owner_graph
    from LinkTwoStockGraph import link_graph, read_link, verify_link
    from ProofModels import AUTHORED
    from ProveTwoStockGraph import make_document, require

    _, probe = import_probes()
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Models.DocumentProvenance",
    ):
        import_module(name)
    for name in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(name)
    attempts = []

    def guard(event, _):
        if event in {
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.fork", "os.posix_spawn", "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("disclosed two-stock generator attempted " + event)

    sys.addaudithook(guard)
    document = make_document(AUTHORED["disclosed-initial"], "disclosed-initial")
    sketches = tuple(
        replace(sketch, name=name)
        for sketch, name in zip(document.sketches, probe.PROFILES, strict=True)
    )
    document = replace(document, metadata={"name": PACKET}, sketches=sketches)
    graph = build_owner_graph(document, 1765500071)
    part = link_graph(graph)
    verify_link(graph, read_link(part), part.keywords)
    require(len(part.streams) == 10 and not attempts, "disclosed candidate generation is unqualified")
    sys.stdout.buffer.write(part.payload)


def prepare(control, stock):
    stock.need(os.name != "nt", "prepare the generated packet on macOS")
    repo = HERE.parents[5]
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=repo, text=True).strip()
    stock.need(
        run(("git", "diff", "--quiet", revision, "--", "src", "re/tooling"), cwd=repo).returncode == 0,
        "candidate implementation differs from its committed revision",
    )
    packet = stock.SHARED / PACKET
    stock.need(not packet.exists(), "the disclosed packet already exists")
    generated = check_output((sys.executable, "-I", "-B", str(HERE), "generate"), timeout=90)
    control.disclosed(stock.SHARED / stock.DISCLOSED)
    packet.mkdir(mode=0o700, exist_ok=False)
    tools = {}
    for source in (HERE, HERE.parent.parent / STOCK, HERE.parent.parent / CONTROL):
        raw = source.read_bytes()
        with (packet / source.name).open("xb") as output:
            output.write(raw)
        tools[source.name] = stock.digest(raw)
    with (packet / PART).open("xb") as output:
        output.write(generated)
    plan = {
        "schema": SCHEMA,
        "revision": revision,
        "candidate_bytes": len(generated),
        "candidate_sha256": stock.digest(generated),
        "control_trial_sha256": stock.TRIAL,
        "tool_sha256": tools,
        "generation_runtime_access_attempts": 0,
        "held_out_sources_read": 0,
    }
    return {**plan, "plan_sha256": stock.publish(packet / "Plan.json", plan)}


def native_candidate(stock, folder, plan, phase):
    import Swapp
    from AuthorCurves import Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor

    stage = folder / phase
    stage.mkdir(exist_ok=False)
    record = Recorder(stage / "Record.json", {"schema": SCHEMA, "phase": phase})
    original = folder.parent / PART
    generated = stock.checked(HERE.with_name(PART), plan["candidate_sha256"])
    saved = folder / "NativeAfterEdit.SLDPRT"
    reopening = phase == "Reopen"
    if reopening:
        previous = stock.prior_phase(folder, "Open")
        stock.need(previous["passed"], "native reopen requires the accepted saved derivative")
        path, pin = saved, previous["result"]["saved_sha256"]
        stock.checked(path, pin)
    else:
        with original.open("xb") as output:
            output.write(generated)
        path, pin = original, plan["candidate_sha256"]
        stock.checked(path, pin)
    result = {"passed": False, "input_sha256": pin, "oracle_build": stock.BUILD}
    controller = author = None
    with AssemblyLoadMonitor() as monitor:
        try:
            record.call("verify the native oracle is idle", Swapp.sweep)
            controller = record.call("start SOLIDWORKS", Swapp.Sw)
            identity = record.call("verify installed executable", application_identity, controller.app)
            stock.need(identity["version_matches"] and identity["file_version"] == stock.BUILD
                       and identity["sha256"] == stock.ORACLE, "the SOLIDWORKS executable differs")
            result["native_identity"] = identity
            author = ThroughAllAuthor(controller.app, record, Swapp)
            model, errors, warnings = record.call("open actual generated or edited path", controller.open, path,
                                                  read_only=reopening)
            author.model = model
            result["open"] = [model is not None, errors, warnings]
            stock.need(result["open"] == [True, 0, 0]
                       and Path(author.get(model, "GetPathName")).samefile(path),
                       "native open did not accept the exact path without warnings")
            predictions = stock.predictions()
            result["before_edit"] = stock.snapshot(author, "fresh open", reopening, predictions, rebuild=True)
            if not reopening:
                stock.edit_stock(author)
                result["after_edit"] = stock.snapshot(author, "moving stock depth edited", True, predictions, rebuild=True)
                stock.need(
                    result["before_edit"]["tree"] == result["after_edit"]["tree"]
                    and result["before_edit"]["profiles"] == result["after_edit"]["profiles"]
                    and not result["after_edit"]["moving_stock_cut"],
                    "the independent stock edit changed the cut scope or feature tree",
                )
                stock.need(not saved.exists(), "the native save destination already exists")
                result["save"] = list(record.call("save edited native derivative", controller.save_as, model, saved))
                stock.need(result["save"] == [True, 0, 0] and saved.is_file()
                           and Path(author.get(model, "GetPathName")).samefile(saved),
                           "edited native derivative did not save cleanly")
                result["saved_sha256"] = stock.digest(saved.read_bytes())
            else:
                stock.need(not result["before_edit"]["moving_stock_cut"],
                           "the unrelated reopened stock has a through-cut face")
            result["passed"] = True
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                if author is not None and author.model is not None:
                    try:
                        record.call("close the native document", controller.close_doc, author.model)
                    except Exception as error:
                        record.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    try:
        stock.checked(path, pin)
        stock.checked(original, plan["candidate_sha256"])
    except ValueError as error:
        record.failure(error)
    result["dialogs"] = monitor.log
    result["passed"] = bool(result["passed"] and not result["dialogs"]
                            and not result.get("controller_diagnostics")
                            and record.data["first_failure"] is None)
    record.data.update(result=result, passed=result["passed"], finished_at=time())
    record.flush()
    return {"phase": phase, "passed": result["passed"], "record_sha256": stock.digest(record.path.read_bytes()),
            "open": result.get("open"), "first_failure": record.data["first_failure"]}


def inspect(control, stock, phase, pin):
    stock.need(os.name == "nt" and HERE.parent.name == PACKET and pin,
               "native inspection requires the frozen Windows packet and exact plan hash")
    plan = json.loads(stock.checked(HERE.with_name("Plan.json"), pin))
    stock.need(plan["schema"] == SCHEMA and plan["control_trial_sha256"] == stock.TRIAL,
               "the trial plan identifies a different experiment")
    for name in (HERE.name, STOCK, CONTROL):
        stock.checked(HERE.with_name(name), plan["tool_sha256"][name])
    trial = HERE.parent.with_name(stock.DISCLOSED)
    controls = control.disclosed(trial)
    sys.path.insert(0, str(trial / "Tools"))
    folder = Path("C:/KitSdkCandidates") / PACKET
    if phase == "before":
        folder.mkdir(exist_ok=False)
    stock.need(folder.is_dir() and not folder.is_symlink(), "bad native trial directory")
    if phase in ("before", "after"):
        return control.measure(folder, phase.capitalize(), trial, controls)
    leading = stock.prior_phase(folder, "Before")
    stock.need(leading["passed"], "the leading native control failed")
    if phase in ("open", "reopen"):
        return native_candidate(stock, folder, plan, phase.capitalize())
    trailing = stock.prior_phase(folder, "After")
    stock.need(trailing["passed"], "the trailing native control failed")
    phases = {}
    for label in ("Before", "Open", "Reopen", "After"):
        receipt = folder / label / "Record.json"
        if receipt.is_file() and not receipt.is_symlink():
            data = stock.prior_phase(folder, label)
            phases[label] = {
                "sha256": stock.digest(receipt.read_bytes()),
                "passed": data["passed"],
                "open": data["result"].get("open"),
                "first_failure": data["first_failure"],
            }
    summary = {
        "schema": SCHEMA,
        "plan_sha256": pin,
        "writer_revision": plan["revision"],
        "candidate_sha256": plan["candidate_sha256"],
        "oracle_sha256": stock.ORACLE,
        "oracle_build": stock.BUILD,
        "controls_passed": True,
        "generated_native_lifecycle_passed": all(phases.get(name, {}).get("passed") for name in ("Open", "Reopen")),
        "phases": phases,
        "held_out_cases": 0,
    }
    stock.publish(folder / "Summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("phase", choices=("generate", "prepare", *PHASES))
    parser.add_argument("--pin")
    args = parser.parse_args()
    if args.phase == "generate":
        generate()
    else:
        control, stock = import_probes()
        result = prepare(control, stock) if args.phase == "prepare" else inspect(control, stock, args.phase, args.pin)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
