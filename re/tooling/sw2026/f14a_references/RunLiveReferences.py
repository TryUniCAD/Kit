from argparse import ArgumentParser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PureWindowsPath
import json
import os
import sys

from ReferenceApi import References, registered, safe_error
from ReferenceControl import control_phase
from ReferencePacket import DRIVERS, PREVIOUS_CAPTURE, PRIOR_WINDOWS, SCHEMA, digest, require, verify, verify_oracle
from ReferenceTopology import COUNTS, Topology


def observe_model(author, bound, dimensions, label, *, rebuilt):
    from AuthorCurves import safe_result
    from AuthorDocumentMassUnits import unit_state
    from InspectFreecadBoxNative import snapshot
    from SdkCornerOwnerGraph import verify_state

    case = bound["case"]
    state = snapshot(author, case)
    signature = verify_state(author, state, case, case["tree"], dimensions, roles=bound["prior_roles"], rebuilt=rebuilt)
    require(safe_result(signature) == bound["prior_signature"], "live rectangle relation owners differ from the exact prior source")
    require(safe_result(unit_state(author, bound["unit_api"])) == bound["prior_units"], "native document units changed")
    author.rec.data["states"][label] = state
    author.rec.flush()
    return {key: state[key] for key in ("configuration", "tree", "body_name", "body_count", "body_topology", "mass", "dimensions")}


def measure_references(author, bound, dimensions, enums, originals, rows, *, baseline=False):
    topology = Topology(author, bound["case"], dimensions, enums)
    extension = author.typed(author.get(author.model, "Extension"), "ModelDocExtension")
    api = References(author, extension, enums)
    producer = {"name": topology.producer_name, "type": topology.producer_type}
    rows.update(producer=producer, by_kind={key: {} for key in COUNTS})
    measure_role(api, topology, ("producer", topology.producer_name), topology.producer, originals, producer, baseline)
    for role, expected in sorted(topology.objects.items()):
        kind, name = role
        row = rows["by_kind"][kind][name] = {"touching_owned_faces": topology.roles[role]}
        measure_role(api, topology, role, expected, originals, row, baseline)
    rows["passed_counts"] = {kind: sum(row["passed"] for row in values.values()) for kind, values in rows["by_kind"].items()}
    rows["passed"] = rows["passed_counts"] == COUNTS and producer["passed"]
    if baseline:
        compare_distinct(api, originals, rows, enums["swObjectEquality"]["swObjectNotSame"])
        rows["passed"] = rows["passed"] and rows["distinct_comparison_passed"]


def measure_role(api, topology, role, expected, originals, row, baseline):
    is_boundary = role[0] != "producer"
    row.update(stage="select_live_entity" if is_boundary else "bind_live_producer", passed=False)
    try:
        selected = topology.select(expected, role[0], row) if is_boundary else expected
        current = api.capture(selected, row)
        if baseline:
            originals[role] = current
        row["stage"] = "match_initial_capture"
        require(role in originals, "no baseline token exists for this native entity")
        api.resolve(originals[role], current, expected, topology, role, row)
        row.update(stage="confirmed", passed=True)
    except Exception as error:
        row["error"] = safe_error(error)
    finally:
        if is_boundary:
            topology.clear()


def compare_distinct(api, originals, rows, different):
    contrasts = rows["distinct_role_checks"] = {}
    for kind in COUNTS:
        pair = sorted(role for role in originals if role[0] == kind)[:2]
        if len(pair) < 2:
            contrasts[kind] = {"passed": False, "available": len(pair)}
            continue
        check = contrasts[kind] = {"roles": [role[1] for role in pair], "passed": False}
        try:
            check["persistent_id_equality"] = api.compare(*(originals[role] for role in pair))
            check["passed"] = check["persistent_id_equality"] == different
        except Exception as error:
            check["error"] = safe_error(error)
    rows["distinct_comparison_passed"] = (all(row["passed"] for row in contrasts.values()) and
                                          len(set(originals.values())) == len(originals) == sum(COUNTS.values()) + 1)


def observe(author, bound, label, dimensions, states, enums, originals, *, rebuild=False, baseline=False, references=True):
    if rebuild:
        require(bool(author.get(author.model, "ForceRebuild3", False)), "live F14a rebuild refused")
    state = states[label] = observe_model(author, bound, dimensions, label, rebuilt=rebuild or label == "Saved")
    if references:
        rows = state["references"] = {"passed": False}
        try:
            measure_references(author, bound, dimensions, enums, originals, rows, baseline=baseline)
        except Exception as error:
            rows.update(passed=False, observation_error=safe_error(error))


def run_lifecycle(controller, author, bound, report, directory, enums, originals, derivative):
    model = author.model
    states = report["states"]
    edited = bound["edited"]
    if derivative is not None:
        observe(author, bound, "FreshOpen", edited, states, enums, originals)
        observe(author, bound, "FreshRebuild", edited, states, enums, originals, rebuild=True, references=False)
        return
    dimensions = bound["case"]["dimensions_m"]
    observe(author, bound, "Initial", dimensions, states, enums, originals, references=False)
    observe(author, bound, "Baseline", dimensions, states, enums, originals, rebuild=True, baseline=True)
    height = author.get(model, "Parameter", DRIVERS[-1])
    status = int(author.get(height, "SetSystemValue3", edited[DRIVERS[-1]],
                            enums["swSetValueInConfiguration_e"]["swSetValue_InThisConfiguration"], author.sw.nothing()))
    report["height_edit"] = {"driver": DRIVERS[-1], "before_m": dimensions[DRIVERS[-1]], "after_m": edited[DRIVERS[-1]], "status": status}
    require(status == enums["swSetValueReturnStatus_e"]["swSetValue_Successful"], "the one native Height edit refused")
    observe(author, bound, "Edited", edited, states, enums, originals, rebuild=True)
    target = directory / "Edited.SLDPRT"
    require(not target.exists(), "the edited native derivative must have a fresh locator")
    author.get(model, "ClearSelection2", True)
    saved = author.rec.call("save one-edit native F14a derivative", controller.save_as, model, target)
    report["save_status"] = list(saved)
    require(saved == (True, 0, 0) and target.stat().st_size > 0 and not target.is_symlink(), "native derivative did not save cleanly")
    require(Path(author.get(model, "GetPathName")).samefile(target), "the live native model did not adopt the distinct derivative locator")
    report["saved_sha256"] = digest(target)
    observe(author, bound, "Saved", edited, states, enums, originals)


def phase(output, bound, enums, originals, derivative=None):
    import Swapp
    from AuthorCurves import Recorder
    from AuthorRectangleAnchors import RectangleAuthor
    from OracleIdentity import application_identity

    role = "EditSave" if derivative is None else "FreshReopen"
    directory = output / role
    directory.mkdir()
    source, expected = (bound["source"], bound["case"]["sha256"]) if derivative is None else derivative
    report = {"input_sha256": expected, "states": {}, "mechanics_passed": False, "passed": False}
    rec = Recorder(directory / "Record.json", {"role": role, "input_sha256": expected})
    rec.data["states"] = {}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == expected, "native phase has another input")
            Swapp.sweep()
            controller = Swapp.Sw()
            report["oracle_identity"] = application_identity(controller.app)
            verify_oracle(report["oracle_identity"])
            require(controller.revision == "34.5.2", "unexpected native COM revision")
            author = RectangleAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open exact native F14a phase", controller.open, source,
                                                       read_only=derivative is not None)
            report.update(open_errors=errors, open_warnings=warnings)
            require(author.model is not None and errors == warnings == 0 and
                    Path(author.get(author.model, "GetPathName")).samefile(source), "native F14a phase did not open cleanly")
            run_lifecycle(controller, author, bound, report, directory, enums, originals, derivative)
            report["mechanics_passed"] = True
        except Exception as error:
            rec.failure(error)
            report["error"] = safe_error(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                report["controller_diagnostics"] = controller.diagnostics
    report.update(dialogs=dialogs.log, immutable_input=source.is_file() and not source.is_symlink() and digest(source) == expected)
    report["mechanics_passed"] = bool(report["mechanics_passed"] and report["immutable_input"] and not dialogs.log and
                                      not rec.data["cleanup_errors"] and not report.get("controller_diagnostics"))
    expected_states = ("FreshOpen",) if derivative is not None else ("Baseline", "Edited", "Saved")
    report["passed"] = report["mechanics_passed"] and all(report["states"][label]["references"]["passed"] for label in expected_states)
    rec.data.update(result=report, passed=report["passed"])
    rec.flush()
    return report | {"record_sha256": digest(rec.path)}


def run(packet, wanted, prior, output, verified):
    require(os.name == "nt" and PureWindowsPath(prior) == PRIOR_WINDOWS,
            "use the exact original Windows F14a packet locator and the pinned Windows oracle")
    require(output.is_absolute() and not output.resolve().is_relative_to(prior.resolve()) and
            not output.resolve().is_relative_to(packet.parent.resolve()), "choose a fresh run sibling outside both immutable packets")
    job, seed, units, bound, previous_api = verified
    sys.path.insert(0, str(prior / "Tools"))
    import Swapp
    from AuthorCurves import write_json
    from AuthorDocumentMassUnits import metadata
    from InspectSdkCornerOwners import control_match

    output.mkdir(exist_ok=False)
    result = {"schema": SCHEMA, "packet_sha256": wanted, "prior_packet_sha256": job["prior_sha256"],
              "previous_capture_result_sha256": PREVIOUS_CAPTURE,
              "heldout_inputs_read": 0, "writer_outputs_generated": 0, "source_reference_transfer_qualified": False,
              "public_writer_qualified": False, "complete_original_corpus_conversions": 0, "cases": {}, "passed": False}
    try:
        try:
            result["pywin32_distribution_version"] = version("pywin32")
        except PackageNotFoundError:
            result["pywin32_distribution_version"] = None
        require(metadata() == units, "the established registered native document API differs")
        result["registered_api"] = registered(Swapp, previous_api)
        enums = result["registered_api"]["enums"]
        try:
            result["control_before"] = control_phase(output, "ControlBefore", seed, enums)
            if result["control_before"]["geometry_passed"]:
                for row in bound:
                    name = row["case"]["id"]
                    work = output / name
                    work.mkdir()
                    observed = result["cases"][name] = {"prior_native_record_sha256": row["prior_sha256"],
                                                        "prior_native_save_sha256": row["prior_edited_sha256"],
                                                        "original_fcstd_sha256": row["case"]["source_sha256"]}
                    originals = {}
                    edited = observed["edit_save"] = phase(work, row, enums, originals)
                    if edited["mechanics_passed"]:
                        derivative = work / "EditSave" / "Edited.SLDPRT", edited["saved_sha256"]
                        observed["fresh_reopen"] = phase(work, row, enums, originals, derivative)
        finally:
            result["control_after"] = control_phase(output, "ControlAfter", seed, enums)
        phases = [result["control_before"], *(case[key] for case in result["cases"].values()
                                              for key in ("edit_save", "fresh_reopen") if key in case), result["control_after"]]
        result["distinct_native_processes"] = len({verify_oracle(row["oracle_identity"]) for row in phases if row.get("oracle_identity")})
        brackets = (phases[0], phases[-1])
        result["controls_healthy"] = all(row["geometry_passed"] for row in brackets) and control_match(*brackets)
        result["reference_transport_controls_passed"] = all(row["reference_transport"]["passed"] for row in brackets)
        Swapp.sweep()
        result["oracle_idle_confirmed"] = True
        result["passed"] = (result["distinct_native_processes"] == len(phases) == 6 and result["controls_healthy"] and
                            all(phase_result["passed"] for phase_result in phases))
        verify(packet, wanted, prior)
        result["immutable_prior_inputs"] = True
    except Exception as error:
        result.update(passed=False, terminal_error=safe_error(error))
    finally:
        write_json(output / "Result.json", result)
    return result


def main():
    parser = ArgumentParser(description="Measure live F14a native persistent references on the exact oracle")
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    verified = verify(args.packet, args.packet_sha256, args.prior)
    if args.action == "verify":
        require(args.output is None or not args.output.exists(), "the run output already exists")
        print(json.dumps({"passed": True, "native_processes_started": 0, "heldout_inputs_read": 0,
                          "original_release_cases": len(verified[3]), "packet_sha256": args.packet_sha256}))
        return 0
    require(args.output is not None, "a fresh output directory is required")
    result = run(args.packet, args.packet_sha256, args.prior, args.output, verified)
    print(json.dumps({"passed": result["passed"], "distinct_native_processes": result.get("distinct_native_processes", 0),
                      "result_sha256": digest(args.output / "Result.json")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
