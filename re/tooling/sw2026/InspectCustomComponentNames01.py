import argparse
import json
from math import pi
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "Baseline/Tools"), str(ROOT / "Baseline/DiagnosticTools")]
import InspectGeneratedConcentric as baseline
import InspectConcentricNames01 as name_probe
from InspectConcentricOpenDiagnostic01 import child_measurement
from CaptureComponentNameApi01 import capture as capture_api
from ConcentricNativeContract import geometric_prediction

ROLES = ("ControlBefore", "Author", "Reopen", "ControlAfter")
BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"


def verify(path, expected):
    baseline.require(
        baseline.digest(path) == expected, "custom-name source packet changed"
    )
    job = json.loads(path.read_bytes())
    baseline.require(
        path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools"
        and job["schema"] == "kit.sw2026.custom-component-name-control.v1"
        and job["roles"] == list(ROLES)
        and job["heldout_inputs_read"]
        == job["writer_outputs"]
        == job["global_preference_changes"]
        == 0
        and job["native_acceptance"] is False,
        "custom-name source scope differs",
    )
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    baseline.verify(ROOT / "Baseline/Trial.json", BASE_TRIAL)
    plan = json.loads((ROOT / "Intent.json").read_bytes())
    baseline.require(
        plan["schema"] == "kit.sw2026.custom-component-name-control-plan.v1"
        and plan["fixed_index"] == 0
        and plan["configuration"] == "Default"
        and plan["rotation"] == "identity on both"
        and plan["mate"]
        == {"alignment": "aligned", "kind": "concentric", "rotation_locked": False}
        and plan["preference_policy"]["changes_authorized"] is False,
        "independent custom-name intent differs",
    )
    return job, plan


def prediction(plan):
    base_job = json.loads((ROOT / "Baseline/Trial.json").read_bytes())
    original = json.loads(
        (
            ROOT / "Baseline" / base_job["cases"]["Feature"]["prediction_path"]
        ).read_bytes()
    )["control"]
    radius, depth = plan["radius_m"], plan["depth_m"]
    baseline.require(
        radius > 0 and depth > 0 and len(set(plan["custom_occurrence_names"])) == 2,
        "independent dimensions or names are invalid",
    )
    transforms = [
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, *point, 1.0, 0.0, 0.0, 0.0]
        for point in plan["translations_m"]
    ]
    geometry = geometric_prediction(radius, plan["center_m"], depth, transforms)
    child_tree = original["child_tree"]
    old = [row["name"] for row in original["occurrences"]]
    replacements = dict(zip(old, plan["custom_occurrence_names"], strict=True))
    tree = [
        [replacements.get(name, name), kind, replacements.get(parent, parent)]
        for name, kind, parent in original["tree"]
    ]
    return {
        "radius_m": radius,
        "depth_m": depth,
        "center_m": plan["center_m"],
        "radial_parameter": "D1@CurveSketch",
        "radial_value_m": radius,
        "depth_parameter": "D1@CurveBoss",
        "parent_configuration": plan["configuration"],
        "child_configuration": plan["configuration"],
        "fixed_index": plan["fixed_index"],
        "occurrences": [
            {"name": name, "transform": matrix}
            for name, matrix in zip(
                plan["custom_occurrence_names"], transforms, strict=True
            )
        ],
        "mate_name": "Concentric1",
        "api_alignment": 0,
        "rotation_locked": False,
        "endpoint_indexes": [0, 1],
        "initial": geometry,
        "tree": tree,
        "child_tree": child_tree,
        "independent_geometry_check": {
            "volume_m3": pi * radius * radius * depth,
            "area_m2": 2 * pi * radius * (radius + depth),
        },
    }


def names_match(author, model, child_path, names, ids):
    snapshot = name_probe.names(author, model, child_path)
    rows = snapshot["references"]
    baseline.require(
        snapshot["observation_complete"]
        and len(rows) == len(names) == len(ids) == 2
        and {row["component_id"] for row in rows} == set(ids),
        "actual matched reference owners differ",
    )
    by_id = {row["component_id"]: row for row in rows}
    for native_id, wanted in zip(ids, names, strict=True):
        row = by_id[native_id]
        baseline.require(
            row["feature_name"] == row["component_name2"] == wanted
            and row["component_path_matches_actual_child"],
            "selected custom name differs through the actual feature/component interfaces",
        )
    return snapshot


def capture_state(author, model, child_path, wanted, ids):
    import Swapp
    from AuthorAssemblySources import feature_tree, transform_matches
    from ConcentricMateEvidence import configuration, mate_state

    assembly = author.typed(model, "AssemblyDoc")
    objects = baseline.components(author, assembly, child_path, wanted)
    child = author.get(objects[0], "GetModelDoc2")
    baseline.require(
        child is not None
        and baseline.same_file(author.get(child, "GetPathName"), child_path),
        "custom control resolved another child",
    )
    configs = [
        configuration(author, model, wanted["parent_configuration"]),
        configuration(author, child, wanted["child_configuration"]),
    ]
    rows = []
    for index, component in enumerate(objects):
        loaded = author.get(component, "GetModelDoc2")
        row = {
            "name": str(author.get(component, "Name2")),
            "native_id": int(author.get(component, "GetID")),
            "configuration": str(author.get(component, "ReferencedConfiguration")),
            "fixed": bool(author.get(component, "IsFixed")),
            "transform": [
                float(value)
                for value in author.get(
                    author.typed(author.get(component, "Transform2"), "MathTransform"),
                    "ArrayData",
                )
            ],
            "visible_child_bodies": (
                len(
                    author.get(author.typed(loaded, "PartDoc"), "GetBodies2", 0, True)
                    or ()
                )
                if loaded is not None
                else 0
            ),
        }
        baseline.require(
            row["native_id"] == ids[index]
            and row["configuration"] == wanted["child_configuration"]
            and row["fixed"] == (index == wanted["fixed_index"])
            and row["visible_child_bodies"] == 1
            and loaded is not None
            and baseline.same_file(author.get(loaded, "GetPathName"), child_path)
            and not author.get(component, "IsSuppressed")
            and not author.get(component, "IsHidden", False)
            and transform_matches(
                row["transform"], wanted["occurrences"][index]["transform"]
            ),
            "custom-name control changed an actual occurrence, configuration or geometry owner",
        )
        rows.append(row)
    child_measure = child_measurement(author, child, wanted)
    actual = author.rec.call(
        "measure actual custom-name parent geometry", Swapp.mass, model
    )
    expected = wanted["initial"]["assembly"]
    baseline.require(
        actual is not None, "custom-name parent mass properties unavailable"
    )
    for key in ("volume", "area"):
        author.rec.close_number(
            "custom-name parent " + key, actual[key], expected[key], absolute=1e-15
        )
    for index in range(3):
        author.rec.close_number(
            "custom-name parent centroid " + str(index),
            actual["com"][index],
            expected["com"][index],
            absolute=1e-12,
        )
    tree = feature_tree(author, model)
    baseline.require(
        [[row["name"], row["type"], row["parent"]] for row in tree] == wanted["tree"],
        "complete custom-name parent tree differs",
    )
    baseline.require(
        int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount"))
        == int(author.get(author.get(child, "Extension"), "GetWhatsWrongCount"))
        == 0,
        "native custom-name control has warnings or errors",
    )
    mate_case = {
        "mate_name": wanted["mate_name"],
        "radius_m": wanted["radius_m"],
        "center_m": wanted["center_m"],
        "lock_rotation": False,
        "api_alignment": 0,
    }
    mate = mate_state(author, model, assembly, child, objects, rows, mate_case)
    baseline.require(
        [row["occurrence_native_id"] for row in mate["ordered_endpoints"]] == ids,
        "actual custom-name mate endpoint order differs",
    )
    return {
        "occurrences": rows,
        "body_count": sum(row["visible_child_bodies"] for row in rows),
        "tree": tree,
        "child_tree": child_measure["tree"],
        "dimensions_m": child_measure["dimensions_m"],
        "mass": {"child": child_measure["mass"], "assembly": actual},
        "configurations": configs,
        "mate": mate,
        "matched_names": names_match(
            author,
            model,
            child_path,
            [row["name"] for row in wanted["occurrences"]],
            ids,
        ),
    }, child


def rename_selected(author, model, component, name, preference):
    import Swapp

    baseline.require(
        not bool(author.get(author.app, "GetUserPreferenceToggle", preference)),
        "component-name update preference must already be false",
    )
    native_id = int(author.get(component, "GetID"))
    author.get(model, "ClearSelection2", True)
    baseline.require(
        bool(author.get(component, "Select4", False, Swapp.nothing(), False)),
        "actual component cannot be selected for rename",
    )
    manager = author.typed(author.get(model, "SelectionManager"), "ISelectionMgr")
    baseline.require(
        int(author.get(manager, "GetSelectedObjectCount2", -1)) == 1,
        "rename selection is not singular",
    )
    selected = author.typed(
        author.get(manager, "GetSelectedObject6", 1, -1), "Component2"
    )
    owner = author.typed(
        author.get(manager, "GetSelectedObjectsComponent4", 1, -1), "Component2"
    )
    baseline.require(
        int(author.get(selected, "GetID"))
        == int(author.get(owner, "GetID"))
        == native_id,
        "rename selection lost its actual occurrence ID",
    )
    row = {
        "native_id": native_id,
        "setter_input": name,
        "before": str(author.get(component, "Name2")),
        "selected_component_id": int(author.get(selected, "GetID")),
    }
    author.rec.data.setdefault("rename_observations", []).append(row)
    author.rec.flush()
    author.rec.call(
        "set actual selected component Name2",
        setattr,
        component,
        "Name2",
        name,
        parameters={"value": name, "native_id": native_id},
    )
    row["after"] = str(author.get(component, "Name2"))
    author.rec.flush()
    baseline.require(
        row["after"] == name,
        "actual Name2 setter did not retain its explicit authored name",
    )
    author.get(model, "ClearSelection2", True)
    baseline.require(
        not bool(author.get(author.app, "GetUserPreferenceToggle", preference)),
        "rename changed the application preference",
    )
    return row


def author_control(author, controller, plan, wanted, preference):
    import Swapp
    from ConcentricMateEvidence import component_map, author_mate
    from ConcentricSourceRuntime import save_pair

    working = ROOT / "Owned/Working"
    working.mkdir(parents=True, exist_ok=False)
    child_path = working / (plan["child_name"] + ".SLDPRT")
    case = {
        "id": "NameControlChild",
        "name": plan["child_name"],
        "plane": "front",
        "profile": {
            "kind": "circle",
            "center_mm": [value * 1000 for value in plan["center_m"]],
            "radius_mm": plan["radius_m"] * 1000,
        },
        "depth_mm": plan["depth_m"] * 1000,
        "end_condition": "blind",
        "reverse": False,
        "expected_bodies": 1,
        "dimension_kind": "radial",
    }
    author.build(case, controller)
    child = author.model
    baseline.require(
        bool(author.get(child, "ForceRebuild3", False)),
        "custom-name cylinder child did not rebuild",
    )
    child_status = list(
        author.rec.call(
            "save new custom-name control child", controller.save_as, child, child_path
        )
    )
    baseline.require(
        child_status == [True, 0, 0], "new custom-name child save failed or warned"
    )
    template = Path(
        author.rec.call(
            "resolve registered custom-name assembly template",
            controller.template,
            "assembly",
        )
    )
    baseline.require(
        template.is_file() and template.suffix.lower() == ".asmdot",
        "registered assembly template unavailable",
    )
    model = author.get(controller.app, "NewDocument", str(template), 0, 0.0, 0.0)
    baseline.require(model is not None, "new custom-name assembly unavailable")
    assembly = author.typed(model, "AssemblyDoc")
    paths = Swapp.VARIANT(
        Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_BSTR, [str(child_path)] * 2
    )
    poses = Swapp.VARIANT(
        Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8,
        [value for row in wanted["occurrences"] for value in row["transform"]],
    )
    origins = Swapp.VARIANT(
        Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_BSTR, [""] * 2
    )
    inserted = author.get(assembly, "AddComponents3", paths, poses, origins)
    baseline.require(
        inserted is not None and len(inserted) == 2,
        "native custom-name insertion count differs",
    )
    mate_case = {
        "child_name": plan["child_name"],
        "radius_m": plan["radius_m"],
        "center_m": plan["center_m"],
        "endpoint_order": [0, 1],
        "api_alignment": 0,
        "lock_rotation": False,
        "mate_name": "Concentric1",
    }
    components = component_map(author, assembly, mate_case, child_path)
    creation = author_mate(author, model, assembly, components, child, mate_case)
    ids = [int(author.get(component, "GetID")) for component in components]
    baseline.require(len(set(ids)) == 2, "native source occurrence IDs collide")
    rows = [
        rename_selected(author, model, component, name, preference)
        for component, name in zip(
            components, plan["custom_occurrence_names"], strict=True
        )
    ]
    baseline.require(
        bool(author.get(model, "ForceRebuild3", False)),
        "custom-name assembly did not rebuild",
    )
    initial, child = capture_state(author, model, child_path, wanted, ids)
    parent_path = ROOT / "Native/Source" / (plan["parent_name"] + ".SLDASM")
    saved_child = parent_path.with_name(plan["child_name"] + ".SLDPRT")
    saved = save_pair(
        author, controller, model, assembly, child, parent_path, saved_child
    )
    final, _ = capture_state(author, model, saved_child, wanted, ids)
    baseline.require(
        baseline.signature(initial) == baseline.signature(final),
        "custom names or native identities changed on synchronized save",
    )
    result = {
        "initial": initial,
        "saved_state": final,
        "saved_files": saved,
        "occurrence_ids": ids,
        "rename": rows,
        "mate_creation": creation,
        "parent_path": str(parent_path),
        "child_path": str(saved_child),
        "writer_outputs": 0,
    }
    baseline.write_json(ROOT / "SavedAuthor.json", result)
    return result


def reopen_control(author, controller, plan, wanted):
    prior = json.loads((ROOT / "Inspection/Author/Result.json").read_bytes())
    baseline.require(prior["passed"] is True, "custom-name author phase has not passed")
    baseline.checked(ROOT / "SavedAuthor.json", prior["saved_author_sha256"])
    authored = json.loads((ROOT / "SavedAuthor.json").read_bytes())
    parent, child = Path(authored["parent_path"]), Path(authored["child_path"])
    for role, path in (("parent", parent), ("child", child)):
        baseline.checked(path, authored["saved_files"][role]["sha256"])
    model, errors, warnings = author.rec.call(
        "fresh open exact custom-name native source",
        controller.open,
        str(parent),
        2,
        read_only=True,
    )
    baseline.require(
        model is not None
        and errors == warnings == 0
        and baseline.same_file(author.get(model, "GetPathName"), parent),
        "custom-name native source fresh open failed or warned",
    )
    first, _ = capture_state(author, model, child, wanted, authored["occurrence_ids"])
    baseline.require(
        bool(author.get(model, "ForceRebuild3", False)),
        "custom-name source fresh rebuild failed",
    )
    rebuilt, _ = capture_state(author, model, child, wanted, authored["occurrence_ids"])
    baseline.require(
        baseline.signature(first)
        == baseline.signature(rebuilt)
        == baseline.signature(authored["saved_state"]),
        "custom-name source lost its tree, identity or endpoints on fresh reopen",
    )
    for role, path in (("parent", parent), ("child", child)):
        baseline.checked(path, authored["saved_files"][role]["sha256"])
    return {"initial": first, "rebuilt": rebuilt, "native_inputs_unchanged": True}


def phase(path, expected, role):
    baseline.require(
        os.name == "nt" and role in ROLES,
        "only root runs the owned custom-name native phase",
    )
    job, plan = verify(path, expected)
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    if role.startswith("Control"):
        row = baseline.phase(ROOT / "Baseline/Trial.json", BASE_TRIAL, "Feature", role)
        result = {
            "role": role,
            "passed": row["passed"],
            "control": row,
            "oracle_identity": row.get("oracle_identity"),
            "numeric_checks": row.get("numeric_checks", 0),
            "native_acceptance": False,
        }
        baseline.write_json(directory / "Result.json", result)
        return result
    before = json.loads((ROOT / "Inspection/ControlBefore/Result.json").read_bytes())
    baseline.require(
        before["control"]["passed"] is True, "source control-before has not passed"
    )
    runtime = job["guest_runtime"]
    baseline.require(
        tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "custom-name guest runtime differs",
    )
    expected_api = json.loads((ROOT / "ApiMetadata.json").read_bytes())
    baseline.require(
        capture_api() == expected_api, "actual registered custom-name API changed"
    )
    preference = expected_api["enums"]["swExtRefUpdateCompNames"]
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(
        directory / "Record.json", {"role": role, "packet_sha256": expected}
    )
    result = {
        "role": role,
        "passed": False,
        "native_acceptance": False,
        "writer_outputs": 0,
        "global_preference_changes": 0,
        "parameter_edits": 0,
    }
    controller = author = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle custom-name source oracle", Swapp.sweep)
            controller = recorder.call(
                "start fresh custom-name source oracle", Swapp.Sw
            )
            identity = recorder.call(
                "verify exact custom-name source oracle",
                application_identity,
                controller.app,
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "unexpected custom-name source oracle",
            )
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            baseline.require(
                int(author.get(controller.app, "GetDocumentCount")) == 0,
                "custom-name source phase is not cold",
            )
            result["name_update_preference"] = bool(
                author.get(controller.app, "GetUserPreferenceToggle", preference)
            )
            baseline.require(
                result["name_update_preference"] is False,
                "swExtRefUpdateCompNames must already be false; no application preference will be changed",
            )
            result.update(
                author_control(author, controller, plan, prediction(plan), preference)
                if role == "Author"
                else reopen_control(author, controller, plan, prediction(plan))
            )
            if role == "Author":
                result["saved_author_sha256"] = baseline.digest(
                    ROOT / "SavedAuthor.json"
                )
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = {"type": type(error).__name__, "error": str(error)}
        finally:
            if author is not None:
                try:
                    result["name_update_preference_after"] = bool(
                        author.get(author.app, "GetUserPreferenceToggle", preference)
                    )
                    baseline.require(
                        result["name_update_preference_after"]
                        == result.get("name_update_preference"),
                        "custom-name source phase changed the application preference",
                    )
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    try:
        verify(path, expected)
        result["immutable_inputs_unchanged"] = True
    except Exception as error:
        recorder.failure(error)
        result["immutable_inputs_unchanged"] = False
    result["passed"] = bool(
        result["passed"]
        and result["immutable_inputs_unchanged"]
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and recorder.data["first_failure"] is None
        and not recorder.data["cleanup_errors"]
    )
    result["numeric_checks"] = len(recorder.data["checks"])
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    baseline.write_json(directory / "Result.json", result)
    return result


def summary(path, expected):
    verify(path, expected)
    rows = {}
    for role in ROLES:
        source = ROOT / "Inspection" / role / "Result.json"
        if source.is_file():
            rows[role] = json.loads(source.read_bytes())
    identities = {
        (row.get("oracle_identity") or {}).get("process_creation_filetime")
        for row in rows.values()
    } - {None}
    healthy = all(
        rows.get(role, {}).get("control", {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    passed = bool(
        healthy
        and len(rows) == len(identities) == 4
        and all(row.get("passed") for row in rows.values())
    )
    result = {
        "schema": "kit.sw2026.custom-component-name-control-result.v1",
        "passed": passed,
        "source_control_qualified": passed,
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "phases": rows,
        "native_acceptance": False,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "global_preference_changes": 0,
        "parameter_edits": 0,
    }
    baseline.write_json(ROOT / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase", choices=ROLES)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        job, plan = verify(path, args.trial_sha256)
        prediction(plan)
        print(
            json.dumps(
                {
                    "verified": True,
                    "native_processes_started": 0,
                    "heldout_inputs_read": 0,
                }
            )
        )
        return 0
    result = (
        phase(path, args.trial_sha256, args.phase)
        if args.command == "phase"
        else summary(path, args.trial_sha256)
    )
    print(json.dumps({"passed": result["passed"], "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
