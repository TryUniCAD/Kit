from argparse import ArgumentParser
from pathlib import Path
import json
import os

from AuthorCurves import Recorder, require, write_json
from AuthorLinearPatternSources import control_phase
from AuthorPatternEnvelope import PatternEnvelopeAuthor
from LinearPatternSpecs import rectangle
from PatternEnvelopePacket import BUILD, CONTROL, ORACLE, checked, digest
from RunPatternEnvelope import installed, saved_hash
from OracleIdentity import application_identity
import Swapp


ROOT = Path(r"C:\KitGeneratedLocalPattern")
CASES = ("ColdRaisedPatternA", "ColdRaisedPatternB")


def author_spec(model, measured, edit):
    plane = model["plane"]
    return {
        "plate_box_m": model["seed"]["plate"]["bounds_m"],
        "seed_box_m": model["seed"]["seed"]["bounds_m"],
        "hinge": {"name": model["axis"], "selection": [{"name": "Right Plane"}, {"name": "Top Plane"}],
                  "axis_model": [0, 0, -1]},
        "direction_datum": {"name": plane["name"], "selection": [{"name": "Right Plane"}, {"name": model["axis"]}],
                            "arguments": [16, plane["angle_rad"], 4, 0.0], "origin_m": [0.0, 0.0, 0.0],
                            "required_signed_normal": measured["signed_direction"]},
        "arms": [{"spacing_m": model["pattern"]["pitch_m"], "count": model["pattern"]["count"]},
                 {"spacing_m": edit["pattern"]["pitch_m"], "count": edit["pattern"]["count"]}],
    }


def measure_geometry(author, expected, stage):
    model = author.model
    body_count = Swapp.bodies(model)
    mass = Swapp.mass(model)
    diagnostics = int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount"))
    feature_rows = Swapp.features(model)
    feature_errors = [row for row in feature_rows if row.get("error") != 0 or row.get("warning") is not False]
    status = {"body_count": body_count, "mass": mass, "rebuild_diagnostics": diagnostics,
              "feature_diagnostics": feature_errors}
    author.rec.data[stage + "_initial_geometry"] = status
    author.rec.flush()
    require(body_count == expected["body_count"] and mass and not mass.get("error") and diagnostics == 0
            and feature_rows and not feature_errors,
            f"{stage} did not publish a healthy joined solid")
    bounds = author.extreme_bounds()
    require(bounds["faces"] == expected["face_count"], f"{stage} face count differs")
    author.rec.close_number(stage + " volume", mass["volume"], expected["volume_m3"], absolute=1e-22)
    author.rec.close_number(stage + " area", mass["area"], expected["area_m2"], absolute=1e-18)
    for index, (actual, target) in enumerate(zip(mass["com"], expected["centroid_m"], strict=True)):
        author.rec.close_number(f"{stage} center of mass {index}", actual, target, absolute=1e-10)
    for index, (actual, target) in enumerate(zip(bounds["minmax"], expected["bounds_m"], strict=True)):
        author.rec.close_number(f"{stage} bound {index}", actual, target, absolute=1e-9)
    return {**status, "face_count": bounds["faces"], "bounds_m": bounds["minmax"]}


def inspect_pattern(author, model):
    plan = model["pattern"]
    name = plan["name"]
    feature = author.get(author.model, "FeatureByName", name)
    require(feature is not None and author.get(feature, "GetTypeName2") == "LPattern",
            "actual linear pattern owner is absent")
    definition = author.typed(author.get(feature, "GetDefinition"), "LinearPatternFeatureData")
    require(author.get(definition, "AccessSelections", author.model, Swapp.nothing()), "pattern definition is inaccessible")
    try:
        axis = author.get(definition, "D1Axis")
        datum, actual_plane = author.direction_plane(author.case)
        axis_ref = author.persistent(axis, "pattern direction plane")
        require(axis_ref["hex"] in (author.persistent(datum, "direction datum feature")["hex"],
                                    author.persistent(actual_plane, "direction datum geometry")["hex"]),
                "pattern selected a different physical direction")
        seed, = author.get(definition, "PatternFeatureArray")
        require(author.get(seed, "Name") == model["seed"]["seed"]["feature"],
                "pattern selected a different physical seed")
        require(author.get(definition, "GetPatternFeatureCount") == 1
                and author.get(definition, "D1TotalInstances") == plan["count"]
                and bool(author.get(definition, "D1ReverseDirection")) is plan["reverse"]
                and author.get(definition, "D1EndCondition") == 0
                and not author.get(definition, "IsDirection2Specified")
                and author.get(definition, "D2Axis") is None
                and not (author.get(definition, "SkippedItemArray") or ()),
                "actual instance, direction or scope differs")
        author.rec.close_number("actual placed pitch", author.get(definition, "D1Spacing"), plan["pitch_m"])
    finally:
        author.get(definition, "ReleaseSelectionAccess")
    drivers = {}
    for label, expected in (("D1", plan["count"]), ("D3", plan["pitch_m"])):
        parameter = author.get(author.model, "Parameter", f"{label}@{name}")
        require(parameter is not None and not author.get(parameter, "ReadOnly") and author.get(parameter, "DrivenState") == 2,
                "pattern driver does not belong to the editable live feature")
        current = float(author.get(parameter, "SystemValue"))
        author.rec.close_number(f"live {label} on {name}", current, expected)
        drivers[label] = current
    parents = tuple(str(author.get(item, "Name")) for item in author.get(feature, "GetParents") or ())
    require(set(parents) == {model["seed"]["seed"]["feature"], model["plane"]["name"]},
            "pattern dependency owners differ")
    return {"name": name, "drivers": drivers, "parents": parents, "native_axis": axis_ref}


def state(author, reference, label):
    model = reference["modeled_input"]
    geometry = measure_geometry(author, reference["independent_cell_measure"], label)
    active = author.get(author.model, "GetActiveConfiguration")
    require(author.get(active, "Name") == model["seed"]["configuration"], "selected configuration differs")
    datum = author.observe_datum()
    require(datum["reverse"] is model["pattern"]["reverse"], "actual signed datum differs")
    names = (model["seed"]["plate"]["sketch"], model["seed"]["plate"]["feature"],
             model["axis"], model["plane"]["name"], model["seed"]["seed"]["sketch"],
             model["seed"]["seed"]["feature"], model["pattern"]["name"])
    tree = author.feature_tree(required_names=names)
    actual = [row["name"] for row in tree if not row["suppressed"] and row["name"] in names]
    require(len(actual) == len(names)
            and actual.index(names[0]) < actual.index(names[1]) < actual.index(names[5]) < actual.index(names[6])
            and actual.index(names[2]) < actual.index(names[3]) < actual.index(names[6])
            and actual.index(names[4]) < actual.index(names[5]), "authored feature order differs")
    for seed in (False, True):
        owner = model["seed"]["seed" if seed else "plate"]
        author.inspect_profile(owner["sketch"], rectangle(author.case, seed))
        author.inspect_feature(owner["feature"], owner["sketch"], owner["bounds_m"][1][2] * 1000, True)
    return {"geometry": geometry, "tree": tree, "pattern": inspect_pattern(author, model), "datum": datum}


def phase(folder, label, source, identity, original, edited, api, *, destination=None):
    rec = Recorder(folder / (label + ".json"), {"phase": label, "source_sha256": identity["sha256"]})
    result = {"passed": False}
    rec.data["result"] = result
    controller = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(not Swapp.application_pids(), "fresh probe requires an idle oracle")
            checked(source, identity["sha256"], identity["bytes"])
            controller = rec.call("launch isolated versioned COM", Swapp.Sw)
            exact = rec.call("verify executable and lifetime", application_identity, controller.app)
            result["identity"] = exact
            require(exact["version_matches"] and exact["file_version"] == BUILD and exact["sha256"] == ORACLE
                    and controller.revision == "34.5.2", "unexpected SOLIDWORKS build")
            model, error, warning = rec.call("open immutable generated part", controller.open, source, read_only=destination is None)
            result["open"] = {"opened": model is not None, "error": error, "warning": warning}
            rec.flush()
            require(model is not None and error == warning == 0, "generated part did not cold open cleanly")
            author = PatternEnvelopeAuthor(controller.app, rec, api["angle"], author_spec(
                original["modeled_input"], original["independent_cell_measure"], edited["modeled_input"]
            ))
            author.connect(model)
            require(Path(author.get(model, "GetPathName")).samefile(source), "opened another locator")
            require(bool(author.get(model, "IsOpenedReadOnly")) is (destination is None),
                    "native document access mode differs")
            current = original if destination else edited
            result["cold_geometry"] = measure_geometry(author, current["independent_cell_measure"], "cold")
            require(author.get(model, "ForceRebuild3", False), "native pattern rebuild failed")
            result["rebuilt"] = state(author, current, "rebuilt")
            if destination:
                param = author.get(model, "Parameter", f'D3@{original["modeled_input"]["pattern"]["name"]}')
                pitch = edited["modeled_input"]["pattern"]["pitch_m"]
                require(author.get(param, "SetSystemValue3", pitch, 1, Swapp.nothing()) == 0
                        and author.get(model, "ForceRebuild3", False), "actual pitch edit failed")
                result["edited"] = state(author, edited, "edited")
                require(result["rebuilt"]["tree"] == result["edited"]["tree"], "live pitch edit changed feature tree")
                require(not destination.exists() and controller.save_as(model, destination) == (True, 0, 0)
                        and Path(author.get(model, "GetPathName")).samefile(destination), "separate native save failed")
                result["saved"] = saved_hash(destination)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    result["passed"] = bool(result["passed"] and not dialogs.log and not rec.data["cleanup_errors"]
                            and not result.get("controller_diagnostics") and not Swapp.application_pids())
    result["first_failure"] = rec.data["first_failure"]
    result["numeric_checks"] = len(rec.data["checks"])
    checked(source, identity["sha256"], identity["bytes"])
    rec.data["passed"] = result["passed"]
    rec.flush()
    return result | {"record_sha256": digest(rec.path.read_bytes())}


def run(packet, pin):
    require(os.name == "nt" and not Swapp.application_pids() and not ROOT.exists(), "fresh Windows oracle required")
    manifest = json.loads(checked(packet / "Packet.json", pin))
    require(manifest["schema"] == "kit.sw2026.generated-raised-pattern-native.v1"
            and manifest["native_build"] == BUILD and manifest["oracle_sha256"] == ORACLE, "incompatible packet")
    for name, value in manifest["files"].items():
        path = (packet / name).resolve(strict=True)
        require(path.is_relative_to(packet), "packet path escaped its owner")
        checked(path, value)
    builds = json.loads(checked(packet / "Build.json", manifest["files"]["Build.json"]))
    plans = builds["model_cases"]
    require(set(plans) == set(CASES) and builds["heldout_cases"] == builds["native_lifecycles"] == 0, "expect disclosed models")
    api = installed(packet)
    seed = packet / "Control.SLDPRT"
    checked(seed, CONTROL)
    ROOT.mkdir()
    output = packet.parent / "NativeResult"
    output.mkdir(exist_ok=False)
    target = output / "Result.json"
    receipt = {"schema": "kit.sw2026.generated-raised-pattern-native-result.v1", "packet_sha256": pin,
               "build_sha256": manifest["files"]["Build.json"], "build": BUILD, "oracle_sha256": ORACLE,
               "heldout_cases": 0, "controls": {}, "phases": {}, "passed": False}
    processes = []

    def control(side):
        row, stamp = control_phase(seed, CONTROL, output / f"Control-{side}.json")
        receipt["controls"][side] = row
        if stamp:
            processes.append(stamp)
        write_json(target, receipt)
        return row["passed"]

    try:
        if control("before"):
            for case in CASES:
                original, edited = (plans[case][key] for key in ("original", "pitch_only"))
                identity = original["native_container"]
                source = ROOT / (case + ".SLDPRT")
                require(str(source) == original["modeled_input"]["seed"]["path"], "embedded source locator differs")
                data = checked(packet / source.name, identity["sha256"], identity["bytes"])
                with source.open("xb") as stream:
                    stream.write(data)
                saved = ROOT / (case + "Edited.SLDPRT")
                changed = phase(output, case + "-edit", source, identity, original, edited, api, destination=saved)
                receipt["phases"][case + "-edit"] = changed
                if changed.get("identity"):
                    processes.append(changed["identity"]["process_creation_filetime"])
                write_json(target, receipt)
                print(json.dumps({"case": case, "phase": "edit", "passed": changed["passed"],
                                  "open": changed.get("open"), "failure": changed.get("first_failure")}), flush=True)
                if changed["passed"]:
                    again = phase(output, case + "-reopen", saved, changed["saved"], original, edited, api)
                    receipt["phases"][case + "-reopen"] = again
                    if again.get("identity"):
                        processes.append(again["identity"]["process_creation_filetime"])
                    write_json(target, receipt)
    finally:
        control("after")
        row = receipt["phases"]
        receipt["distinct_processes"] = len(set(processes))
        receipt["passed"] = (all(value["passed"] for value in receipt["controls"].values()) and len(row) == 4
                             and all(value["passed"] for value in row.values()) and processes == sorted(set(processes))
                             and len(processes) == 6)
        write_json(target, receipt)
    return int(not receipt["passed"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.packet.resolve(), args.pin))
