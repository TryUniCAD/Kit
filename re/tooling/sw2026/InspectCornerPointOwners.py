from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import time

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE, RectangleAuthor, control


SCHEMA = "kit.sw2026.corner-point-owner-probe.v1"
TOOLS = {"AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
         "InspectCornerPointOwners.py"}


def checked(root, name, expected):
    path = (root / name).resolve(strict=True)
    curves.require(path.parent == root and curves.digest(path) == expected, "point-owner probe custody differs: " + name)
    return path


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, expected).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
                   "expected an exact disclosed source and generated origin-point owner probe")
    tools = root / "Tools"
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == TOOLS,
                   "point-owner probe requires its entire frozen controller")
    for name, digest in job["tools_sha256"].items():
        checked(tools, name, digest)
    curves.require(set(job["inputs_sha256"]) == {"Control.SLDPRT", "NativeCorner.SLDPRT", "Candidate.SLDPRT", "FailedResult.json",
                   "OriginalPacket.json", "Cases.json", "ArchiveReferenceProof.json"}, "point-owner probe input roles differ")
    for name, digest in job["inputs_sha256"].items():
        checked(root, name, digest)
    curves.require(job["inputs_sha256"]["Control.SLDPRT"] == CONTROL and
                   job["inputs_sha256"]["FailedResult.json"] == "4fa47be9efb275bf5e8be234ca0213f20458a1ce2fdb7b3fc5627a774dc33547",
                   "point-owner probe does not bind the retained healthy failed trial")
    failed = json.loads((root / "FailedResult.json").read_bytes())
    predecessor = json.loads((root / "OriginalPacket.json").read_bytes())
    curves.require(not failed["passed"] and failed["controls_healthy"] and failed["generated_unchanged"] and
                   failed["frozen_inputs_unchanged"] and failed["packet_sha256"] == job["inputs_sha256"]["OriginalPacket.json"] and
                   predecessor["inputs_sha256"]["Candidate.SLDPRT"] == job["inputs_sha256"]["Candidate.SLDPRT"] and
                   len(failed["edits"]) == 3 and all(row["edit"]["open_errors"] == row["edit"]["open_warnings"] == 0 and
                   row["edit"].get("edit_status") is None and row["edit"].get("save_status") is None for row in failed["edits"]),
                   "retained trial is not the exact pre-edit observer failure")
    cases = json.loads((root / "Cases.json").read_bytes())
    reference = json.loads((root / "ArchiveReferenceProof.json").read_bytes())
    curves.require([row["role"] for row in cases] == ["NativeCorner", "Generated"] and
                   PureWindowsPath(cases[1]["open_path"]) == PureWindowsPath(r"C:\KitSdkCandidates\F14aSizedDiscovery.SLDPRT") and
                   all(row["input_sha256"] == job["inputs_sha256"][row["packet_input"]] == reference[row["role"]]["input_sha256"]
                       for row in cases), "point-owner probe cases differ from their exact archive inputs")
    return job, cases


def point_info(author, point, selected_origin, origin_owner):
    typed = author.typed(point, "SketchPoint")
    owner = author.get(typed, "GetSketch")
    return {"id": list(author.get(point, "GetID")), "type": int(author.get(typed, "Type")),
            "position_m": author.point(typed), "same_origin_raw": int(author.get(author.app, "IsSame", selected_origin, point)),
            "same_self_raw": int(author.get(author.app, "IsSame", typed, typed)), "owner_null": owner is None,
            "owner_same_profile_raw": None if owner is None else int(author.get(author.app, "IsSame", owner, author.sketch)),
            "owner_same_origin_raw": None if owner is None or origin_owner is None else int(author.get(author.app, "IsSame", owner, origin_owner)),
            "owner_same_self_raw": None if owner is None else int(author.get(author.app, "IsSame", owner, owner))}


def snapshot(author, case):
    profile = author.get(author.model, "FeatureByName", case["profile"])
    origin_feature = author.get(author.model, "FeatureByName", case["origin"])
    curves.require(profile is not None and origin_feature is not None, "point-owner source lacks its actual named features")
    author.sketch = author.get(profile, "GetSpecificFeature2")
    author.get(author.model, "ClearSelection2", True)
    extension = author.get(author.model, "Extension")
    curves.require(author.get(extension, "SelectByID2", "Point1@" + case["origin"], "EXTSKETCHPOINT", 0.0, 0.0, 0.0,
                              False, 0, author.sw.nothing(), 0), "actual model-origin selection failed")
    selection = author.get(author.model, "SelectionManager")
    selected = author.typed(author.get(selection, "GetSelectedObject6", 1, -1), "SketchPoint")
    origin_owner = author.get(selected, "GetSketch")
    result = {"profile_feature_id": int(author.get(profile, "GetID")), "origin_feature_id": int(author.get(origin_feature, "GetID")),
              "profile_name": case["profile"], "origin_name": case["origin"],
              "profile_owner_same_self_raw": int(author.get(author.app, "IsSame", author.sketch, author.sketch)),
              "selected_origin": point_info(author, selected, selected, origin_owner), "point_enumerations": {}, "coincidences": []}
    for method in ("GetSketchPoints2", "GetSketchPoints"):
        result["point_enumerations"][method] = [point_info(author, point, selected, origin_owner)
                                                for point in author.get(author.sketch, method) or ()]
    manager = author.get(author.sketch, "RelationManager")
    for relation in author.get(manager, "GetRelations", 0) or ():
        if int(author.get(relation, "GetRelationType")) == 9:
            entities = list(author.get(relation, "GetEntities") or ())
            kinds = list(author.get(relation, "GetEntitiesType") or ())
            curves.require(len(entities) == len(kinds) == int(author.get(relation, "GetEntitiesCount")),
                           "point-owner coincidence enumeration is incomplete")
            result["coincidences"].append({"kind": 9, "suppressed": bool(author.get(relation, "Suppressed")),
                                            "entity_types": kinds, "points": [point_info(author, entity, selected, origin_owner) for entity in entities]})
    result["geometry"] = author.geometry()
    result["relations"] = author.relation_graph()
    result["tree"] = author.feature_tree(required_names=(case["profile"], case["feature"], case["origin"]))
    result["constraint_status"] = int(author.get(author.sketch, "GetConstrainedStatus"))
    result["body_count"] = len(author.get(author.typed(author.model, "PartDoc"), "GetBodies2", 0, True) or ())
    result["mass"] = author.rec.call("measure point-owner diagnostic solid", author.sw.mass, author.model)
    result["dimensions_m"] = {name: float(author.get(author.get(author.model, "Parameter", name), "SystemValue"))
                               for name in case["parameter_names"]}
    author.get(author.model, "ClearSelection2", True)
    return result


def measure(author, state, case):
    width, height, depth = case["dimensions_m"]
    curves.require(state["constraint_status"] == 3 and state["body_count"] == 1 and len(state["relations"]) == 7 and
                   len(state["coincidences"]) == 1 and state["coincidences"][0]["entity_types"] == [2, 2] and
                   not state["coincidences"][0]["suppressed"], "point-owner diagnostic lacks its fully constrained ordinary corner")
    curves.require(len(state["geometry"]) == 4 and all(row["kind"] == "line" and not row["construction"] for row in state["geometry"]),
                   "point-owner diagnostic changed the actual contour")
    intended = [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]]
    for side in ("start", "end"):
        for row in state["geometry"]:
            distances = [sum((a - b) ** 2 for a, b in zip(row[side], point, strict=True)) for point in intended]
            curves.require(min(distances) < 1e-20, "point-owner diagnostic has an unexpected contour endpoint")
            point = intended[distances.index(min(distances))]
            for actual, expected in zip(row[side], point, strict=True):
                author.rec.close_number("point-owner corner", actual, expected)
    for name, value in zip(case["parameter_names"], case["dimensions_m"], strict=True):
        author.rec.close_number(name, state["dimensions_m"][name], value)
    for name, value in (("volume", width * height * depth), ("area", 2 * (width * height + width * depth + height * depth)),
                        ("mass", width * height * depth * case["density_kg_m3"])):
        author.rec.close_number("point-owner " + name, state["mass"][name], value, absolute=1e-16)
    for value, expected in zip(state["mass"]["com"], (width / 2, height / 2, depth / 2), strict=True):
        author.rec.close_number("point-owner centre", value, expected)


def phase(output, role, path, case):
    import Swapp
    from OracleIdentity import application_identity

    work = output / role
    work.mkdir()
    rec = curves.Recorder(work / "Record.json", {"role": role, "source": str(path), "source_sha256": case["input_sha256"]})
    result = {"passed": False, "states": {}}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(path) == case["input_sha256"], "point-owner source changed")
            rec.call("require idle point-owner oracle", Swapp.sweep)
            controller = rec.call("launch fresh point-owner oracle", Swapp.Sw)
            identity = rec.call("bind exact point-owner oracle", application_identity, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2",
                           "point-owner oracle version differs")
            author = RectangleAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open immutable point-owner input", controller.open, path, read_only=True)
            result.update(open_errors=errors, open_warnings=warnings)
            curves.require(author.model is not None and errors == warnings == 0 and
                           Path(author.get(author.model, "GetPathName")).samefile(path), "point-owner input load failed or warned")
            for label in ("Initial", "Rebuilt"):
                if label == "Rebuilt":
                    curves.require(author.get(author.model, "ForceRebuild3", False), "point-owner diagnostic rebuild failed")
                state = result["states"][label] = snapshot(author, case)
                rec.data["result"] = result
                rec.flush()
                measure(author, state, case)
            result["passed"] = True
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
    result.update(dialogs=dialogs.log, immutable_input=curves.digest(path) == case["input_sha256"])
    result["passed"] = bool(result["passed"] and result["immutable_input"] and not result["dialogs"] and
                            not result.get("controller_diagnostics") and not rec.data["cleanup_errors"])
    rec.data.update(result=result, passed=result["passed"], numeric_check_count=len(rec.data["checks"]))
    rec.flush()
    return result | {"record_sha256": curves.digest(rec.path)}


def run(packet, expected):
    curves.require(os.name == "nt", "point-owner probe runs only in the root-owned COM oracle")
    job, cases = verify(packet, expected)
    root = packet.parent
    generated = Path(cases[1]["open_path"])
    curves.require(generated.is_file() and curves.digest(generated) == cases[1]["input_sha256"],
                   "the failed trial's exact C path is missing or changed, no path is overwritten")
    output = root / "Inspection"
    output.mkdir()
    result = {"schema": SCHEMA, "packet_sha256": expected, "phases": {}, "passed": False, "heldout_inputs_read": 0,
              "writer_changed": False, "edits_attempted": 0, "saves_attempted": 0, "started_at": time.time()}
    phases = result["phases"]
    try:
        phases["ControlBefore"] = control(output, "ControlBefore", root / "Control.SLDPRT")
        curves.write_json(output / "Result.json", result)
        if phases["ControlBefore"]["passed"]:
            for case in cases:
                path = generated if case["role"] == "Generated" else root / case["packet_input"]
                phases[case["role"]] = phase(output, case["role"], path, case)
                curves.write_json(output / "Result.json", result)
                if not phases[case["role"]]["passed"]:
                    break
    finally:
        phases["ControlAfter"] = control(output, "ControlAfter", root / "Control.SLDPRT")
        result["controls_healthy"] = all(phases[name]["passed"] for name in ("ControlBefore", "ControlAfter"))
        result["distinct_processes"] = len({row.get("oracle_identity", {}).get("process_creation_filetime")
                                           for row in phases.values()} - {None})
        result["inputs_unchanged"] = verify(packet, expected)[0] == job and curves.digest(generated) == cases[1]["input_sha256"]
        result["passed"] = bool(result["controls_healthy"] and len(phases) == result["distinct_processes"] == 4 and
                                all(row["passed"] for row in phases.values()) and result["inputs_unchanged"])
        result["finished_at"] = time.time()
        curves.write_json(output / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Read actual corner-relation point owners without changing a dimension or saving")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        value = {"passed": True, "native_processes_started": 0}
    else:
        result = run(packet, args.packet_sha256)
        value = {key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}
    print(json.dumps(value, sort_keys=True))
    return 0 if value["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
