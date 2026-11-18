from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import os

from AuthorCurves import CurveAuthor, Recorder, digest, require, write_json
from AuthorDocumentMassUnits import TOOLS, checked, metadata, unit_state
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.generated-custom-mass-part-native.v1"
METHODS = TOOLS | {"InspectGeneratedCustomMassUnits.py"}


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(root, path.name, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and job["control_sha256"] == CONTROL and job["heldout_inputs_read"] == 0,
            "custom mass native packet differs")
    require(Path(__file__).resolve().parent == root / "Tools" and set(job["tools_sha256"]) == METHODS,
            "use the exact frozen custom mass method")
    for name, sha in job["tools_sha256"].items():
        checked(root, Path("Tools") / name, sha)
    api = json.loads(checked(root, "DocumentUnitApi.json", job["api_sha256"]).read_bytes())
    seed = checked(root, "Control.SLDPRT", CONTROL)
    shapes = {}
    for case in job["cases"]:
        source = checked(root, case["input"], case["sha256"])
        require(source.stem == case["name"] and case["mass"] in ("g", "kg")
                and len(case["dimensions_m"]) == 3 and all(type(value) is float and value > 0
                                                          for value in case["dimensions_m"])
                and 0 < case["edit_depth_m"] != case["dimensions_m"][2], "generated unit case geometry differs")
        dimensions = shapes.setdefault(case["name"], {})
        require(case["mass"] not in dimensions, "custom mass case repeats a mass choice")
        dimensions[case["mass"]] = case["dimensions_m"]
    require(len(job["cases"]) == 4 and len(shapes) == 2 and all(
        set(dimensions) == {"g", "kg"} and dimensions["g"] == dimensions["kg"]
        for dimensions in shapes.values()
    ), "custom mass packet needs two complete paired designs")
    return root, job, seed, api


def inspect_model(author, api, case, depth):
    model = author.model
    require(author.get(model, "ForceRebuild3", False), "generated unit model did not rebuild")
    extension = author.get(model, "Extension")
    require(author.get(extension, "GetWhatsWrongCount") == 0, "generated unit model has rebuild diagnostics")
    preferences = unit_state(author, api)
    values = api["enums"]
    mass_key = "swUnitsMassPropMass_Grams" if case["mass"] == "g" else "swUnitsMassPropMass_Kilograms"
    require(preferences["swUnitSystem"] == values["swUnitSystem_e"]["swUnitSystem_Custom"]
            and preferences["swUnitsMassPropMass"] == values["swUnitsMassPropMass_e"][mass_key]
            and preferences["swUnitsLinear"] == values["swLengthUnit_e"]["swMM"]
            and preferences["swUnitsAngular"] == values["swAngleUnit_e"]["swDEGREES"],
            "native document did not retain its selected custom mass and linear units")
    parameter = author.get(model, "Parameter", "D1@Boss-Extrude1")
    require(parameter is not None and author.get(parameter, "DrivenState") == 2
            and not author.get(parameter, "ReadOnly"), "generated custom mass depth is not editable")
    author.rec.close_number("native editable depth", author.get(parameter, "SystemValue"), depth)
    body = author.get(author.typed(model, "PartDoc"), "GetBodies2", 0, False)
    require(len(body or ()) == 1, "generated custom mass part requires one solid")
    results = author.rec.call("measure exact native SI geometry", author.sw.mass, model)
    width, height, _ = case["dimensions_m"]
    author.rec.close_number("native custom mass volume", results["volume"], width * height * depth, absolute=1e-16)
    author.rec.close_number("native custom mass surface", results["area"], 2 * (width * height + width * depth + height * depth))
    for axis, observed, target in zip(("x", "y", "z"), results["com"], (0.0, 0.0, depth / 2), strict=True):
        author.rec.close_number("native custom mass centroid " + axis, observed, target)
    return {
        "preferences": preferences, "geometry_m": results, "depth_m": depth, "body_count": 1,
        "tree": author.feature_tree(required_names=("Sketch1", "Boss-Extrude1")),
    }


def phase(directory, source, expected, api, case, previous=None):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir(parents=True, exist_ok=False)
    rec = Recorder(directory / "Record.json", {"role": "generated" if previous is None else "reopen",
                                               "name": case["name"], "mass": case["mass"]})
    result = {"passed": False, "identity": None}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == expected, "custom unit input changed")
            rec.call("guard fresh custom mass oracle", Swapp.sweep)
            controller = rec.call("start custom mass oracle", Swapp.Sw)
            identity = rec.call("bind native custom mass executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE
                    and controller.revision == "34.5.2", "unexpected custom mass native build")
            result["identity"] = identity
            author = CurveAuthor(controller.app, rec, Swapp)
            author.model, error, warning = rec.call("open exact custom mass part", controller.open, source, read_only=previous is not None)
            result["open_diagnostics"] = [error, warning]
            require(author.model is not None and error == warning == 0
                    and Path(author.get(author.model, "GetPathName")).samefile(source), "custom mass native open failed or warned")
            depth = case["dimensions_m"][2] if previous is None else case["edit_depth_m"]
            initial = inspect_model(author, api, case, depth)
            result["initial"] = initial
            if previous is None:
                parameter = author.get(author.model, "Parameter", "D1@Boss-Extrude1")
                changed = author.get(parameter, "SetSystemValue3", case["edit_depth_m"], 1, author.sw.nothing())
                require(changed == 0, "native custom mass depth edit failed")
                edited = inspect_model(author, api, case, case["edit_depth_m"])
                require(edited["tree"] == initial["tree"] and edited["preferences"] == initial["preferences"],
                        "custom mass edit changed unit settings or modeled feature tree")
                result["edited"] = edited
                target = directory / (source.stem + ".SLDPRT")
                require(not target.exists(), "custom mass save target already exists")
                saved = rec.call("save generated custom mass edition", controller.save_as, author.model, target)
                require(saved == (True, 0, 0) and target.is_file() and target.stat().st_size > 0,
                        "generated custom mass edition did not save cleanly")
                result.update(saved_sha256=digest(target), saved_bytes=target.stat().st_size, save_diagnostics=list(saved))
            else:
                require(initial["tree"] == previous["edited"]["tree"]
                        and initial["preferences"] == previous["edited"]["preferences"],
                        "separate native reopen changed the edited model or unit preferences")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                        author.model = None
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(source_unchanged=digest(source) == expected, numeric_checks=len(rec.data["checks"]),
                  dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and result["source_unchanged"] and not result["dialogs"]
                            and not rec.data["cleanup_errors"] and not result.get("controller_diagnostics"))
    rec.data.update(result=result, passed=result["passed"])
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def run(path, expected):
    require(os.name == "nt", "generated custom mass lifecycle requires the pinned Windows oracle")
    root, job, seed, api = verify(path, expected)
    require(api == metadata(), "registered custom mass API changed after packet preparation")
    output = root / "Inspection"
    output.mkdir(exist_ok=False)
    phases = {}
    result = {"schema": SCHEMA, "packet_sha256": expected, "phases": phases, "passed": False,
              "heldout_inputs_read": 0, "public_writer_qualified": False}

    def add(key, value):
        phases[key] = value
        write_json(output / "Result.json", result)

    try:
        add("ControlBefore", control(output, "ControlBefore", seed))
        if phases["ControlBefore"]["passed"]:
            for case in job["cases"]:
                role = case["name"] + "-" + case["mass"]
                source = checked(root, case["input"], case["sha256"])
                first = phase(output / role / "Initial", source, case["sha256"], api, case)
                add(role + "/Initial", first)
                if first["passed"]:
                    saved = output / role / "Initial" / source.name
                    reopened = phase(output / role / "Reopen", saved, first["saved_sha256"], api, case, first)
                    add(role + "/Reopen", reopened)
    finally:
        add("ControlAfter", control(output, "ControlAfter", seed))
    verify(path, expected)
    identities = [row.get("identity", row.get("oracle_identity")) for row in phases.values()]
    seen = {(row["process_id"], row["process_creation_filetime"]) for row in identities if row is not None}
    result["controls_healthy"] = all(phases[control_role]["passed"] for control_role in ("ControlBefore", "ControlAfter"))
    result["distinct_native_processes"] = len(seen)
    result["passed"] = len(seen) == len(phases) == 10 and all(row["passed"] for row in phases.values())
    write_json(output / "Result.json", result)
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure a generated custom mass part through native edit and fresh reopen")
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.action == "verify":
        root, _, _, _ = verify(args.packet, args.packet_sha256)
        require(not (root / "Inspection").exists(), "custom mass native output root is already used")
        print(json.dumps({"passed": True, "processes_started": 0}))
    else:
        result = run(args.packet, args.packet_sha256)
        print(json.dumps({"passed": result["passed"], "processes": result["distinct_native_processes"]}))
        raise SystemExit(0 if result["passed"] else 3)
