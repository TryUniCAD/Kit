from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

import AuthorCurves as curves
from AuthorPartProperties import SUMMARY_FIELDS, dispatch_property, manager, read_text
from AuthorRectangleAnchors import CONTROL, ORACLE, RectangleAuthor
from InspectSdkCornerOwners import control_match, control_phase, snapshot as rectangle_snapshot
from SdkCornerOwnerGraph import geometry_roles, verify_state


SCHEMA = "kit.sw2026.sdk-freecad-origin-box-discovery.v1"
TOOLS = {"AuthorCurves.py", "AuthorPartProperties.py", "AuthorRectangleAnchors.py", "InspectFresh.py",
         "InspectSdkBlindPart.py", "InspectSdkCornerOwners.py", "InspectCornerPointOwners.py", "OracleIdentity.py",
         "SdkCornerOwnerGraph.py", "Swapp.py", "InspectFreecadBoxNative.py"}


def checked(root, name, digest):
    path = (root / name).resolve(strict=True)
    curves.require(path.parent == root and path.is_file() and curves.digest(path) == digest,
                   "FreeCAD box packet identity differs: " + name)
    return path


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, expected).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0
                   and not job["fcstd_conversion_accepted"], "expected the controlled disclosed FreeCAD origin-box trial")
    tools = root / "Tools"
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == TOOLS,
                   "FreeCAD box trial requires its exact observer closure")
    for name, digest in job["tools_sha256"].items():
        checked(tools, name, digest)
    inputs = job["inputs_sha256"]
    expected_inputs = {"Control.SLDPRT", "Candidate.SLDPRT", "BuildSource.json", "Case.json", "Build.json"}
    if job.get("observer_retry"):
        expected_inputs.add("FirstTrialResult.json")
    curves.require(set(inputs) == expected_inputs
                   and inputs["Control.SLDPRT"] == CONTROL, "FreeCAD box trial source roles differ")
    evidence = {name: checked(root, name, digest) for name, digest in inputs.items()}
    build = json.loads(evidence["Build.json"].read_bytes())
    case = json.loads(evidence["Case.json"].read_bytes())
    names = [case["parameter_bindings"][source_id] for source_id in case["ordered_source_parameters"]]
    curves.require(build["passed"] and build["runtime_input_file_reads"] == 0 and build["native_acceptance"] is False
                   and build["sha256"] == inputs["Candidate.SLDPRT"] and build["bytes"] == evidence["Candidate.SLDPRT"].stat().st_size
                   and build["source_sha256"] == case["source_sha256"]
                   and build["origin_coincidence"]["actual_owner_aliases"] and build["origin_coincidence"]["origin_relations"] == 1
                   and build["parameter_bindings"] == case["parameter_bindings"] and case["parameter_names"] == names
                   and [case["dimensions_m"][name] * 1000 for name in names] == build["source_dimensions_mm"]
                   and case["source_text"] == build["source_text"] and len(build["streams"]) == 12,
                   "FreeCAD box candidate does not bind its actual source and guarded build")
    location = PureWindowsPath(build["native_path"])
    curves.require(location.parent == PureWindowsPath(r"C:\KitFreecadBox121") and location.name == case["name"] + ".SLDPRT",
                   "FreeCAD box candidate lacks its exact isolated native identity")
    curves.require(case["density_kg_m3"] == 1 and case["document_preference_density_kg_m3"] == 1000,
                   "this unassigned part profile requires the separately measured density owners")
    if job.get("observer_retry"):
        prior = json.loads(evidence["FirstTrialResult.json"].read_bytes())
        measured = prior["phases"]["Generated"]
        curves.require(prior["packet_sha256"] == job["observer_retry"]["first_packet_sha256"]
                       and prior["controls_healthy"] and prior["first_generation_immutable"] and not prior["passed"]
                       and measured["open_errors"] == measured["open_warnings"] == 0 and "anchored mass" in measured["error"]
                       and measured["states"]["Initial"]["body_count"] == 1
                       and measured["states"]["Initial"]["mass"]["mass"] == measured["states"]["Initial"]["mass"]["volume"],
                       "observer-only retry must retain the exact first density-owner failure")
    return job, case, evidence, location


def snapshot(author, case):
    state = rectangle_snapshot(author, case)
    model = author.model
    part = author.typed(model, "PartDoc")
    bodies = author.get(part, "GetBodies2", 0, False) or ()
    curves.require(len(bodies) == 1, "FreeCAD box target must have one actual solid")
    body = author.typed(bodies[0], "Body2")
    state["body_name"] = str(author.get(body, "Name"))
    state["body_type"] = int(author.get(body, "GetType"))
    state["body_topology"] = [int(author.get(body, method)) for method in ("GetVertexCount", "GetEdgeCount", "GetFaceCount")]
    file_owner = manager(author, model, "")
    file_text = {name: read_text(author, file_owner, name) for name in author.get(file_owner, "GetNames") or ()}
    summary = {name: str(dispatch_property(author, model, "SummaryInfo", index))
               for name, index in SUMMARY_FIELDS.items()}
    expected = case["source_text"]
    curves.require(state["body_type"] == 0 and state["body_topology"] == [8, 12, 6], "FreeCAD box topology differs")
    state["document_density_preference_kg_m3"] = float(
        author.get(author.get(model, "Extension"), "GetUserPreferenceDouble", 7, 0)
    )
    author.rec.close_number("document density preference", state["document_density_preference_kg_m3"],
                            case["document_preference_density_kg_m3"])
    curves.require(set(file_text) == set(expected["file"]) and
                   all(file_text[name]["raw"] == file_text[name]["resolved"] == value and
                       file_text[name]["type"] == 30 and not file_text[name]["linked"]
                       for name, value in expected["file"].items()) and
                   all(summary[name] == value for name, value in expected["summary"].items()),
                   "FreeCAD authored summary or file text differs")
    state.update(native_summary=summary, native_file_text=file_text)
    return state


def phase(output, role, source, digest, case, prior=None):
    import Swapp
    from OracleIdentity import application_identity

    work = output / role
    work.mkdir()
    rec = curves.Recorder(work / "Record.json", {"role": role, "input_sha256": digest})
    result = {"role": role, "passed": False, "states": {}}
    rec.data["result"] = result
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == digest, "changed FreeCAD box measurement input")
            rec.call("guard idle FreeCAD box oracle", Swapp.sweep)
            controller = rec.call("start fresh FreeCAD box oracle", Swapp.Sw)
            identity = rec.call("bind exact FreeCAD box oracle", application_identity, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == ORACLE and
                           controller.revision == "34.5.2", "unexpected FreeCAD box oracle build")
            author = RectangleAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open exact FreeCAD box target", controller.open, source,
                                                       read_only=prior is not None)
            result.update(open_errors=errors, open_warnings=warnings)
            curves.require(author.model is not None and errors == warnings == 0 and
                           Path(author.get(author.model, "GetPathName")).samefile(source), "FreeCAD box did not open cleanly")
            values = case["dimensions_m"] if prior is None else prior["saved_dimensions_m"]
            roles = None if prior is None else prior["roles"]
            signature = None if prior is None else prior["signature"]

            def observe(label, wanted, rebuild):
                nonlocal roles, signature
                if rebuild:
                    curves.require(author.get(author.model, "ForceRebuild3", False), "FreeCAD box target did not rebuild")
                state = result["states"][label] = snapshot(author, case)
                rec.flush()
                if roles is None:
                    roles = geometry_roles(state["geometry"], case["vertices_m"])
                seen = verify_state(author, state, case, case["tree"], wanted, roles=roles, rebuilt=rebuild)
                if signature is None:
                    signature = seen
                curves.require(seen == signature, "FreeCAD box target changed actual parametric owners")

            def change(name, value):
                driver = author.get(author.model, "Parameter", name)
                status = int(author.get(driver, "SetSystemValue3", value, 1, Swapp.nothing()))
                curves.require(status == 0, "FreeCAD box driving edit failed: " + name)

            observe("Initial", values, False)
            observe("Rebuilt", values, True)
            if prior is None:
                for name, value in zip(case["parameter_names"], case["edit_values_m"], strict=True):
                    edited = dict(values, **{name: value})
                    change(name, value)
                    observe("Edited " + name, edited, True)
                    if name != case["parameter_names"][-1]:
                        change(name, values[name])
                        observe("Restored " + name, values, True)
                derivative = work / "Edited.SLDPRT"
                status = rec.call("save edited FreeCAD box target", controller.save_as, author.model, derivative)
                curves.require(status == (True, 0, 0) and derivative.stat().st_size > 0, "FreeCAD box target did not save cleanly")
                result.update(saved_sha256=curves.digest(derivative), saved_dimensions_m=edited, save_status=list(status))
            result.update(passed=True, roles=roles, signature=signature)
        except Exception as error:
            rec.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, immutable_input=curves.digest(source) == digest)
    result["passed"] = bool(result["passed"] and result["immutable_input"] and not result["dialogs"] and
                            not result.get("controller_diagnostics") and not rec.data["cleanup_errors"])
    rec.flush()
    return result | {"record_sha256": curves.digest(rec.path), "checks": len(rec.data["checks"])}


def run(packet, wanted):
    curves.require(os.name == "nt", "use the pinned Windows oracle for FreeCAD box verification")
    job, case, evidence, location = verify(packet, wanted)
    output = packet.parent / "Inspection"
    output.mkdir()
    report = {"schema": SCHEMA, "packet_sha256": wanted, "phases": {}, "passed": False,
              "fcstd_conversion_accepted": False, "public_writer_qualified": False, "heldout_inputs_read": 0}

    def checkpoint():
        curves.write_json(output / "Result.json", report)

    checkpoint()
    rows = report["phases"]
    seed = evidence["Control.SLDPRT"]
    candidate = Path(location)
    digest = job["inputs_sha256"]["Candidate.SLDPRT"]
    try:
        rows["ControlBefore"] = control_phase(output, "ControlBefore", seed)
        checkpoint()
        if rows["ControlBefore"]["passed"]:
            if job.get("observer_retry"):
                curves.require(candidate.is_file() and curves.digest(candidate) == digest,
                               "observer retry requires the existing exact generated file")
            else:
                candidate.parent.mkdir()
                with evidence["Candidate.SLDPRT"].open("rb") as src, candidate.open("xb") as dst:
                    copyfileobj(src, dst)
            first = rows["Generated"] = phase(output, "Generated", candidate, digest, case)
            checkpoint()
            if first["passed"]:
                rows["FreshReopen"] = phase(output, "FreshReopen", output / "Generated" / "Edited.SLDPRT",
                                             first["saved_sha256"], case, prior=first)
    except Exception as error:
        report["error"] = repr(error)
    finally:
        rows["ControlAfter"] = control_phase(output, "ControlAfter", seed)
        report["controls_healthy"] = bool(rows.get("ControlBefore", {}).get("passed") and
                                           rows["ControlAfter"]["passed"] and control_match(rows["ControlBefore"], rows["ControlAfter"]))
        report["distinct_processes"] = len({(identity["process_id"], identity["process_creation_filetime"])
                                             for row in rows.values() if (identity := row.get("oracle_identity"))})
        report["inputs_immutable"] = all(curves.digest(path) == job["inputs_sha256"][name] for name, path in evidence.items())
        report["first_generation_immutable"] = candidate.is_file() and curves.digest(candidate) == digest
        report["passed"] = bool(report["controls_healthy"] and report["inputs_immutable"] and
                                report["first_generation_immutable"] and report["distinct_processes"] == len(rows) == 4
                                and all(row["passed"] for row in rows.values()) and not report.get("error"))
        checkpoint()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        verify(packet, arguments.packet_sha256)
        raise SystemExit(0)
    result = run(packet, arguments.packet_sha256)
    print(json.dumps({"passed": result["passed"], "distinct_processes": result["distinct_processes"]}))
    raise SystemExit(0 if result["passed"] else 3)
