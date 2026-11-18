from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.part-property-source.v1"
TOOLS = {
    "AuthorCurves.py", "AuthorPartProperties.py", "AuthorRectangleAnchors.py",
    "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
}
SUMMARY_FIELDS = {"title": 0, "subject": 1, "author": 2, "keywords": 3, "comments": 4}
TEXT_PROPERTY = 30


def checked(root, name, expected):
    path = (root / name).resolve(strict=True)
    curves.require(path.parent == root and path.is_file() and curves.digest(path) == expected,
                   f"property source custody is invalid for {name}")
    return path


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, expected).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
                   and job["heldout_inputs_read"] == 0 and job["control_sha256"] == CONTROL,
                   "expected the exact disclosed property source protocol")
    tools = (root / "Tools").resolve(strict=True)
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == TOOLS,
                   "the property source observer is outside its frozen tool closure")
    for name, digest in job["tools_sha256"].items():
        checked(tools, name, digest)
    seed = checked(root, "Control.SLDPRT", CONTROL)
    cases = job["cases"]
    curves.require(len(cases) == 2 and len({case["name"] for case in cases}) == 2
                   and len({case["input_sha256"] for case in cases}) == 2
                   and len({len(case["document"]) for case in cases}) == 2,
                   "two unrelated disclosed source designs must exercise distinct property counts")
    for case in cases:
        checked(root, case["input"], case["input_sha256"])
        curves.require(case["name"].isascii() and case["name"].isalpha() and case["configuration"]
                       and set(case["summary"]) <= SUMMARY_FIELDS.keys(),
                       "property case name or summary field is invalid")
        for scope in ("summary", "document", "configured"):
            curves.require(all(isinstance(value, str) and value for value in case[scope].values()),
                           "every authored property value must be nonempty text")
    return root, seed, cases


def dispatch_property(author, obj, name, index, *values):
    raw = obj._oleobj_
    dispid = raw.GetIDsOfNames(name)
    flags = author.sw.pythoncom.DISPATCH_PROPERTYPUT if values else author.sw.pythoncom.DISPATCH_PROPERTYGET
    return author.rec.call(name, raw.Invoke, dispid, 0, flags, not values, index, *values,
                           parameters={"index": index, "values": list(values), "dispatch_flags": flags})


def manager(author, model, configuration):
    extension = author.get(model, "Extension")
    return author.sw.wc.Dispatch(dispatch_property(author, extension, "CustomPropertyManager", configuration))


def read_text(author, owner, name):
    sw = author.sw
    raw, resolved = [sw.VARIANT(sw.pythoncom.VT_BYREF | sw.pythoncom.VT_BSTR, "") for _ in range(2)]
    evaluated, linked = sw.byref_bool(), sw.byref_bool()
    code = int(author.get(owner, "Get6", name, False, raw, resolved, evaluated, linked))
    return {"type": int(author.get(owner, "GetType2", name)), "raw": str(raw.value),
            "resolved": str(resolved.value), "evaluated": bool(evaluated.value),
            "linked": bool(linked.value), "status": code}


def snapshot(author, model, owners, case):
    configuration = author.get(model, "GetActiveConfiguration")
    state = {
        "summary": {name: str(dispatch_property(author, model, "SummaryInfo", index))
                    for name, index in SUMMARY_FIELDS.items()},
        "configuration": str(author.get(configuration, "Name")),
        "body_count": len(author.get(author.typed(model, "PartDoc"), "GetBodies2", 0, True) or ()),
        "diagnostic_count": int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount")),
        "tree": author.feature_tree(required_names=case["required_features"]),
        "mass": author.rec.call("measure the unchanged source solid", author.sw.mass, model),
    }
    for scope, owner in owners.items():
        state[scope] = {name: read_text(author, owner, name) for name in author.get(owner, "GetNames") or ()}
    curves.require(state["configuration"] == case["configuration"] and state["body_count"] == 1
                   and state["diagnostic_count"] == 0 and state["mass"]["volume"] > 0,
                   "property source must remain the actual healthy one-solid part")
    return state


def check_properties(state, case):
    for name, value in case["summary"].items():
        curves.require(state["summary"][name] == value, f"native summary field {name} differs")
    for scope in ("document", "configured"):
        for name, value in case[scope].items():
            item = state[scope][name]
            curves.require(item["type"] == TEXT_PROPERTY and item["raw"] == item["resolved"] == value
                           and not item["linked"],
                           f"native {scope} property {name} differs in value, type or linkage")


def check_shape(rec, first, last):
    curves.require(first["tree"] == last["tree"], "property changes altered the actual native feature tree")
    for name in ("mass", "area", "volume"):
        rec.close_number("unchanged " + name, last["mass"][name], first["mass"][name], absolute=1e-16)
    for index, (actual, expected) in enumerate(zip(last["mass"]["com"], first["mass"]["com"], strict=True)):
        rec.close_number(f"unchanged centre {index}", actual, expected)


def phase(output, role, source, expected, case, baseline=None):
    import Swapp
    from OracleIdentity import application_identity

    directory = output / role
    directory.mkdir()
    rec = curves.Recorder(directory / "Record.json", {"role": role, "source_sha256": expected})
    result = {"passed": False}
    rec.data["result"] = result
    controller = model = author = owners = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == expected, "property phase source hash changed")
            rec.call("guard the fresh property oracle", Swapp.sweep)
            controller = rec.call("start fresh property oracle", Swapp.Sw)
            identity = rec.call("bind executable and process", application_identity, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == ORACLE
                           and controller.revision == "34.5.2", "unexpected property oracle version")
            model, error, warning = rec.call("open disclosed part", controller.open, source, read_only=baseline is not None)
            result["open_diagnostics"] = [error, warning]
            curves.require(model is not None and error == warning == 0, "property source failed clean open")
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            author.model = model
            curves.require(Path(author.get(model, "GetPathName")).samefile(source), "property oracle opened another file")
            owners = {"document": manager(author, model, ""), "configured": manager(author, model, case["configuration"])}
            initial = snapshot(author, model, owners, case)
            result["initial"] = initial
            if baseline is None:
                for name, value in case["summary"].items():
                    dispatch_property(author, model, "SummaryInfo", SUMMARY_FIELDS[name], value)
                for scope, owner in owners.items():
                    for name, value in case[scope].items():
                        status = int(author.get(owner, "Add3", name, TEXT_PROPERTY, value, 0))
                        curves.require(status == 0, f"native property insertion failed for {scope}:{name}")
            curves.require(author.get(model, "ForceRebuild3", False), "property source failed rebuild")
            rebuilt = snapshot(author, model, owners, case)
            result["rebuilt"] = rebuilt
            check_properties(rebuilt, case)
            check_shape(rec, initial, rebuilt)
            if baseline is None:
                target = directory / (case["name"] + ".SLDPRT")
                curves.require(not target.exists(), "property derivative destination already exists")
                status = rec.call("save disclosed property derivative", controller.save_as, model, target)
                result["save_status"] = list(status)
                curves.require(status == (True, 0, 0) and target.stat().st_size > 0, "property derivative did not save cleanly")
                result.update(saved_name=target.name, saved_sha256=curves.digest(target))
            else:
                check_properties(initial, case)
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
                  progress_windows=dialogs.progress, checks=len(rec.data["checks"]))
    result["passed"] = bool(result["passed"] and result["unchanged"] and not result["dialogs"]
                            and not result.get("application_diagnostics") and not rec.data["cleanup_errors"])
    rec.data["passed"] = result["passed"]
    rec.flush()
    return result | {"record_sha256": curves.digest(rec.path)}


def run(packet, expected):
    curves.require(os.name == "nt", "native part property discovery requires the pinned Windows oracle")
    root, seed, cases = verify(packet, expected)
    output = root / "Inspection"
    output.mkdir()
    phases = {}
    result = {"schema": SCHEMA, "packet_sha256": expected, "heldout_inputs_read": 0, "passed": False, "phases": phases}

    def add(role, value):
        phases[role] = value
        curves.write_json(output / "Result.json", result)

    try:
        add("ControlBefore", control(output, "ControlBefore", seed))
        if phases["ControlBefore"]["passed"]:
            for case in cases:
                role = case["name"] + "Author"
                source = checked(root, case["input"], case["input_sha256"])
                authored = phase(output, role, source, case["input_sha256"], case)
                add(role, authored)
                if authored["passed"]:
                    derivative = output / role / authored["saved_name"]
                    reopened = phase(output, case["name"] + "Reopen", derivative,
                                     authored["saved_sha256"], case, authored["rebuilt"])
                    add(case["name"] + "Reopen", reopened)
    finally:
        add("ControlAfter", control(output, "ControlAfter", seed))
        verify(packet, expected)
        counts = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values()
                  if row.get("oracle_identity")}
        result["controls_healthy"] = all(phases.get(role, {}).get("passed") for role in ("ControlBefore", "ControlAfter"))
        result["distinct_processes"] = len(counts)
        result["passed"] = len(counts) == len(phases) == 6 and all(row["passed"] for row in phases.values())
        curves.write_json(output / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.action == "verify":
        verify(packet, args.packet_sha256)
        print(json.dumps({"verified": True, "processes_started": 0}))
        return 0
    result = run(packet, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
