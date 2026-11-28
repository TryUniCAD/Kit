from __future__ import annotations

import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

import AuthorCurves as curves
from AuthorPartProperties import check_properties, check_shape, dispatch_property, manager, read_text, snapshot
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.sdk-part-property-native.v1"
TOOLS = {"AuthorCurves.py", "AuthorPartProperties.py", "AuthorRectangleAnchors.py",
         "InspectFresh.py", "InspectGeneratedPartProperties.py", "OracleIdentity.py", "Swapp.py"}


def checked(root, name, digest):
    path = (root / name).resolve(strict=True)
    curves.require(path.is_relative_to(root) and path.is_file() and curves.digest(path) == digest,
                   f"generated property packet input changed: {name}")
    return path


def verify(packet, expected, verify_targets):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, expected).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
                   and job["heldout_inputs_read"] == 0 and job["control_sha256"] == CONTROL,
                   "the property trial requires the pinned disclosed profile")
    tools = (root / "Tools").resolve(strict=True)
    curves.require(Path(__file__).resolve().parent == tools and set(job["tool_sha256"]) == TOOLS,
                   "property trial tool closure differs")
    for name, digest in job["tool_sha256"].items():
        checked(tools, name, digest)
    source = checked(root, "Control.SLDPRT", CONTROL)
    cases = job["cases"]
    curves.require(len(cases) == 2 and {row["profile"] for row in cases} == {"polygon", "circle"},
                   "property trial requires two independently defined shape profiles")
    for case in cases:
        candidate = checked(root, case["file"], case["file_sha256"])
        build_file = checked(root, case["build"], case["build_sha256"])
        repeated = checked(root, case["repeat"], case["build_sha256"])
        request = json.loads(checked(root, case["request"], case["request_sha256"]).read_bytes())
        build = json.loads(build_file.read_bytes())
        document = request["document"]
        config, = document["configurations"]["$tuple"]
        curves.require(build_file.read_bytes() == repeated.read_bytes() and build["passed"]
                       and build["runtime_input_file_reads"] == 0 and len(build["stream_sha256"]) == 13
                       and build["file_sha256"] == case["file_sha256"]
                       and b64decode(build["file_base64"], validate=True) == candidate.read_bytes(),
                       "candidate differs from its two guarded model-only builds")
        curves.require(case["summary"] == document["metadata"]["document_summary"]
                       and case["document"] == document["metadata"]["custom_properties"]
                       and case["configured"] == config["attributes"]["custom_properties"]
                       and case["configuration"] == config["name"],
                       "property expectations differ from the actual neutral input")
        location = PureWindowsPath(build["native_path"])
        curves.require(str(location) == case["native_path"] and location.parent == PureWindowsPath(r"C:\KitSdkCandidates")
                       and location.name == document["metadata"]["name"] + ".SLDPRT" == candidate.name,
                       "expected the exact unique native candidate location")
        shared = case["shared_property"]
        curves.require(shared in case["document"] and shared in case["configured"]
                       and len({case["document"][shared], case["configured"][shared],
                                case["new_document_value"], case["new_configuration_value"]}) == 4,
                       "the test requires two independently observable scopes of one name")
        if verify_targets and os.name == "nt":
            curves.require(not Path(case["native_path"]).exists(), "native property candidate path already exists")
    return root, job, source


def check_geometry(rec, state, expected):
    mass = state["mass"]
    for key in ("volume", "area"):
        rec.close_number("calculated solid " + key, mass[key], expected[key], absolute=1e-16)
    for index, (actual, target) in enumerate(zip(mass["com"], expected["com"], strict=True)):
        rec.close_number(f"calculated solid centroid {index}", actual, target)


def updated_case(case):
    changed = deepcopy(case)
    changed["document"][case["shared_property"]] = case["new_document_value"]
    changed["configured"][case["shared_property"]] = case["new_configuration_value"]
    return changed


def edit(author, owners, case):
    shared = case["shared_property"]
    patterns = (("document", "new_document_value", "configured", case["configured"][shared]),
                ("configured", "new_configuration_value", "document", case["new_document_value"]))
    for scope, name, sibling, expected in patterns:
        status = int(author.get(owners[scope], "Set2", shared, case[name]))
        curves.require(status == 0 and read_text(author, owners[scope], shared)["raw"] == case[name]
                       and read_text(author, owners[sibling], shared)["raw"] == expected,
                       "the property edit did not isolate its exact scope")


def phase(output, role, source, expected, case, baseline=None):
    import Swapp
    from OracleIdentity import application_identity

    directory = output / role
    directory.mkdir()
    rec = curves.Recorder(directory / "Record.json", {"role": role, "input_sha256": expected})
    result = {"passed": False, "states": {}}
    rec.data["result"] = result
    controller = model = author = owners = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == expected, "working property candidate hash differs")
            rec.call("guard fresh generated property oracle", Swapp.sweep)
            controller = rec.call("start generated property oracle", Swapp.Sw)
            identity = rec.call("bind native process and executable", application_identity, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == ORACLE
                           and controller.revision == "34.5.2", "unexpected generated property oracle version")
            model, error, warning = rec.call("open exact property candidate", controller.open, source, read_only=baseline is not None)
            result["open_diagnostics"] = [error, warning]
            curves.require(model is not None and error == warning == 0, "native property candidate opened with diagnostics")
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            author.model = model
            curves.require(Path(author.get(model, "GetPathName")).samefile(source), "native property trial opened another file")
            owners = {"document": manager(author, model, ""), "configured": manager(author, model, case["configuration"])}
            initial = snapshot(author, model, owners, case)
            result["states"]["initial"] = initial
            rec.flush()
            changed = updated_case(case)
            check_properties(initial, case if baseline is None else changed)
            check_geometry(rec, initial, case["geometry"])
            if baseline is None:
                edit(author, owners, case)
            curves.require(author.get(model, "ForceRebuild3", False), "generated property candidate did not rebuild")
            rebuilt = snapshot(author, model, owners, case)
            result["states"]["rebuilt"] = rebuilt
            rec.flush()
            check_properties(rebuilt, changed)
            check_shape(rec, initial, rebuilt)
            check_geometry(rec, rebuilt, case["geometry"])
            if baseline is None:
                target = directory / (source.stem + "Edited.SLDPRT")
                status = rec.call("persist generated text edits", controller.save_as, model, target)
                result["save_status"] = status
                curves.require(status == (True, 0, 0) and target.is_file(), "generated property model failed native save")
                result.update(saved_name=target.name, saved_sha256=curves.digest(target))
            else:
                check_shape(rec, baseline, rebuilt)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
            result["error"] = repr(error)
        finally:
            owners = author = None
            if controller is not None:
                try:
                    if model is not None:
                        controller.close_doc(model)
                        model = None
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["application_diagnostics"] = controller.diagnostics
    result.update(unchanged=curves.digest(source) == expected, dialogs=dialogs.log,
                  progress_windows=dialogs.progress, numeric_checks=len(rec.data["checks"]))
    result["passed"] = bool(result["passed"] and result["unchanged"] and not result["dialogs"]
                            and not result.get("application_diagnostics") and not rec.data["cleanup_errors"])
    rec.data["passed"] = result["passed"]
    rec.flush()
    return result | {"record_sha256": curves.digest(rec.path)}


def run(packet, expected):
    curves.require(os.name == "nt", "generated property measurement requires the pinned Windows oracle")
    root, job, seed = verify(packet, expected, True)
    output = root / "Inspection"
    output.mkdir()
    phases = {}
    report = {"schema": SCHEMA, "packet_sha256": expected, "phases": phases, "passed": False,
              "heldout_inputs_read": 0, "public_writer_qualified": False}

    def add(role, value):
        phases[role] = value
        curves.write_json(output / "Result.json", report)

    try:
        add("ControlBefore", control(output, "ControlBefore", seed))
        if phases["ControlBefore"]["passed"]:
            for case in job["cases"]:
                native = Path(case["native_path"])
                path = root / case["file"]
                native.parent.mkdir(exist_ok=True)
                with path.open("rb") as source, native.open("xb") as target:
                    copyfileobj(source, target)
                role = case["profile"] + "Edit"
                first = phase(output, role, native, case["file_sha256"], case)
                add(role, first)
                if first["passed"]:
                    saved = output / role / first["saved_name"]
                    add(case["profile"] + "Reopen", phase(output, case["profile"] + "Reopen", saved,
                                                         first["saved_sha256"], case, first["states"]["rebuilt"]))
    except Exception as error:
        report["error"] = repr(error)
    finally:
        add("ControlAfter", control(output, "ControlAfter", seed))
        verify(packet, expected, False)
        report["controls_healthy"] = all(phases[key]["passed"] for key in ("ControlBefore", "ControlAfter"))
        identities = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values()
                      if row.get("oracle_identity")}
        report["distinct_processes"] = len(identities)
        report["passed"] = len(identities) == len(phases) == 6 and all(row["passed"] for row in phases.values())
        curves.write_json(output / "Result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.action == "verify":
        verify(packet, args.packet_sha256, True)
        print(json.dumps({"verified": True, "processes_started": 0}))
        return 0
    result = run(packet, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
