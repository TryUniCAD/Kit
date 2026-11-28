from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE
from InspectSdkCornerOwners import control_match, control_phase


SCHEMA = "kit.sw2026.native-part-driver-names-discovery.v1"
TOOLS = {"AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "InspectSdkBlindPart.py",
         "InspectSdkCornerOwners.py", "InspectCornerPointOwners.py", "OracleIdentity.py", "SdkCornerOwnerGraph.py",
         "Swapp.py", "AuthorPartDriverNames.py"}


def checked(folder, name, expected):
    path = (folder / name).resolve(strict=True)
    curves.require(path.parent == folder and path.is_file() and curves.digest(path) == expected,
                   "part name research input changed: " + name)
    return path


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    deck = json.loads(checked(root, packet.name, expected).read_bytes())
    curves.require(deck["schema"] == SCHEMA and deck["oracle_sha256"] == ORACLE and deck["heldout_inputs_read"] == 0,
                   "name experiment must use the disclosed source lane")
    toolbox = root / "Tools"
    curves.require(Path(__file__).resolve().parent == toolbox and set(deck["tools_sha256"]) == TOOLS,
                   "name experiment requires the pinned native driver source")
    tools = {name: checked(toolbox, name, digest) for name, digest in deck["tools_sha256"].items()}
    sample = checked(root, "Control.SLDPRT", CONTROL)
    cases = deck["cases"]
    curves.require(len(cases) == 2 and len({case["source_sha256"] for case in cases}) == 2,
                   "name experiment requires two unrelated disclosed part identities")
    for case in cases:
        checked(root, case["source"], case["source_sha256"])
        curves.require(len(case["drivers"]) == 3 and all(re.fullmatch(r"[A-Za-z]{3,20}", row["new_name"]) and
                       row["original_name"] in ("D1", "D2") for row in case["drivers"]) and
                       len({row["new_name"] for row in case["drivers"]}) == 3 and
                       case["drivers"][0]["feature"] == case["drivers"][1]["feature"] != case["drivers"][2]["feature"] and
                       re.fullmatch(r"[A-Za-z ]{3,40}", case["body_name"]),
                       "name experiment uses three distinct unexpressed driver labels and one ordinary body name")
    return deck, sample


def find_body(author):
    part = author.typed(author.model, "PartDoc")
    bodies = author.get(part, "GetBodies2", 0, False) or ()
    visible = author.get(part, "GetBodies2", 0, True) or ()
    curves.require(len(bodies) == len(visible) == 1, "name trial requires one visible solid")
    body = author.typed(bodies[0], "Body2")
    curves.require(author.get(body, "GetType") == 0, "observed body is not a solid")
    return body


def driver(author, row, renamed):
    name = row["new_name"] if renamed else row["original_name"]
    query = name + "@" + row["feature"]
    dimension = author.get(author.model, "Parameter", query)
    curves.require(dimension is not None and str(author.get(dimension, "Name")) == name and
                   int(author.get(dimension, "DrivenState")) == 2 and not bool(author.get(dimension, "ReadOnly")),
                   "named dimension must retain its live driving property: " + query)
    full = str(author.get(dimension, "FullName")).split("@")
    curves.require(full[:2] == [name, row["feature"]] and len(full) >= 3,
                   "actual named dimension owner differs: " + query)
    return dimension, float(author.get(dimension, "SystemValue"))


def measure(author, case, renamed):
    names = [(row["new_name"] if renamed else row["original_name"]) + "@" + row["feature"] for row in case["drivers"]]
    body = find_body(author)
    tree = author.feature_tree(required_names=tuple(dict.fromkeys(row["feature"] for row in case["drivers"])))
    curves.require(not any(row["error"] or row["warning"] or row["suppressed"] for row in tree),
                   "rename trial feature tree has diagnostics")
    pressure = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
    curves.require(pressure == 0, "rename trial model has diagnostic state")
    return {"body_name": str(author.get(body, "Name")),
            "drivers_m": {name: driver(author, row, renamed)[1] for name, row in zip(names, case["drivers"], strict=True)},
            "tree": [[row["name"], row["type"], row["parent"]] for row in tree],
            "mass": author.rec.call("measure actual named solid", author.sw.mass, author.model)}


def save(author, controller, target):
    curves.require(not target.exists(), "part name output already exists")
    result = author.rec.call("save separate part name comparison", controller.save_as, author.model, target)
    curves.require(result == (True, 0, 0) and target.stat().st_size > 0, "part name save failed or warned")
    return curves.digest(target)


def compare(author, prior, current, case):
    curves.require(current["body_name"] == case["body_name"] and current["tree"] == prior["tree"],
                   "explicit body name or modeled feature tree was lost")
    for old, name in zip(prior["drivers_m"].values(), current["drivers_m"], strict=True):
        author.rec.close_number("identical renamed parameter", current["drivers_m"][name], old)
    for key in ("volume", "area", "mass"):
        author.rec.close_number("unchanged " + key, current["mass"][key], prior["mass"][key], absolute=1e-16)
    for actual, expected in zip(current["mass"]["com"], prior["mass"]["com"], strict=True):
        author.rec.close_number("unchanged centroid", actual, expected)


def run_phase(folder, case, source, expected, prior=None):
    import Swapp
    from OracleIdentity import application_identity

    folder.mkdir(parents=True)
    mode = "renamed" if prior is None else "reopen"
    rec = curves.Recorder(folder / "Record.json", {"mode": mode, "source_sha256": expected})
    result = {"passed": False}
    rec.data["result"] = result
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == expected, "part names source hash changed")
            rec.call("guard idle named part oracle", Swapp.sweep)
            controller = rec.call("launch fresh named part oracle", Swapp.Sw)
            identity = rec.call("bind named part oracle", application_identity, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2",
                           "part name oracle build differs")
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            author.model, error, warning = rec.call("open actual named part", controller.open, source, read_only=prior is not None)
            result["open"] = [error, warning]
            curves.require(author.model is not None and error == warning == 0 and
                           Path(author.get(author.model, "GetPathName")).samefile(source),
                           "named part did not open cleanly")
            curves.require(author.get(author.model, "ForceRebuild3", False), "named part did not rebuild")
            if prior is None:
                result["baseline"] = measure(author, case, False)
                result["baseline_sha256"] = save(author, controller, folder / "Baseline.SLDPRT")
                for item in case["drivers"]:
                    dimension, _ = driver(author, item, False)
                    author.set(dimension, "Name", item["new_name"])
                author.set(find_body(author), "Name", case["body_name"])
                author.get(author.get(author.model, "FeatureManager"), "UpdateFeatureTree")
                curves.require(author.get(author.model, "ForceRebuild3", False), "renamed part did not rebuild")
                result["renamed"] = measure(author, case, True)
                compare(author, result["baseline"], result["renamed"], case)
                result["renamed_sha256"] = save(author, controller, folder / "Renamed.SLDPRT")
            else:
                result["reopened"] = measure(author, case, True)
                compare(author, prior["renamed"], result["reopened"], case)
                item = case["drivers"][-1]
                dimension, depth = driver(author, item, True)
                actual = author.get(dimension, "SetSystemValue3", depth * 1.25, 1, Swapp.nothing())
                curves.require(actual == 0 and author.get(author.model, "ForceRebuild3", False),
                               "reopened named depth did not edit and rebuild")
                result["edited"] = measure(author, case, True)
                curves.require(result["edited"]["body_name"] == case["body_name"] and result["edited"]["tree"] == result["reopened"]["tree"],
                               "named body or feature identity changed through an independent edit")
                author.rec.close_number("edited named depth", driver(author, item, True)[1], depth * 1.25)
                author.rec.close_number("edited named prism volume", result["edited"]["mass"]["volume"],
                                        result["reopened"]["mass"]["volume"] * 1.25, absolute=1e-16)
            result["passed"] = True
        except Exception as error:
            result["exception"] = repr(error)
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["input_immutable"] = curves.digest(source) == expected
    result["passed"] = bool(result["passed"] and result["input_immutable"] and not dialogs.log and
                            not result.get("controller_diagnostics") and not rec.data["cleanup_errors"])
    rec.flush()
    return result | {"record_sha256": curves.digest(rec.path)}


def execute(packet, expected):
    curves.require(os.name == "nt", "part names research requires the exact root-owned oracle")
    deck, seed = verify(packet, expected)
    work = packet.parent / "Inspection"
    work.mkdir()
    report = {"schema": SCHEMA, "packet_sha256": expected, "controls": [], "cases": [],
              "passed": False, "heldout_acceptance": False, "fcstd_conversions": 0}

    def checkpoint():
        curves.write_json(work / "Result.json", report)

    try:
        before = control_phase(work, "ControlBefore", seed)
        report["controls"].append(before)
        checkpoint()
        if before["passed"]:
            for case in deck["cases"]:
                paths = work / case["name"]
                source = checked(packet.parent, case["source"], case["source_sha256"])
                renamed = run_phase(paths / "Author", case, source, case["source_sha256"])
                entry = {"name": case["name"], "author": renamed}
                report["cases"].append(entry)
                checkpoint()
                if renamed["passed"]:
                    entry["reopen"] = run_phase(paths / "Fresh", case, paths / "Author" / "Renamed.SLDPRT",
                                                renamed["renamed_sha256"], prior=renamed)
                checkpoint()
    finally:
        after = control_phase(work, "ControlAfter", seed)
        report["controls"].append(after)
        report["controls_healthy"] = len(report["controls"]) == 2 and all(c["passed"] for c in report["controls"]) and control_match(*report["controls"])
        results = report["controls"] + [phase for row in report["cases"] for phase in (row.get("author"), row.get("reopen")) if phase]
        identities = {tuple((i["process_id"], i["process_creation_filetime"]))
                      for phase in results if (i := phase.get("oracle_identity"))}
        report["distinct_processes"] = len(identities)
        report["passed"] = report["controls_healthy"] and len(identities) == len(results) == 6 and all(p["passed"] for p in results)
        checkpoint()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    packet = args.packet.resolve()
    if args.verify_only:
        verify(packet, args.packet_sha256)
        raise SystemExit(0)
    result = execute(packet, args.packet_sha256)
    print(json.dumps({"passed": result["passed"], "distinct_processes": result["distinct_processes"]}))
    raise SystemExit(0 if result["passed"] else 3)
