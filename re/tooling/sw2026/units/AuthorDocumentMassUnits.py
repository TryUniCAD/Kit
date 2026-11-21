from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os

from AuthorCurves import Recorder, digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, RectangleAuthor, control
from DocumentUnitApi import metadata


SCHEMA = "kit.sw2026.document-mass-units-native.v1"
TOOLS = {
    "AuthorDocumentMassUnits.py", "DocumentUnitApi.py", "AuthorCurves.py",
    "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
}
MODES = ("MillimeterGram", "CustomGram", "CustomKilogram")
PREFERENCES = (
    "swUnitSystem", "swUnitsLinear", "swUnitsAngular", "swUnitsLinearDecimalPlaces",
    "swUnitsAngularDecimalPlaces", "swUnitsDualLinear", "swUnitsMassPropLength",
    "swUnitsMassPropMass", "swUnitsMassPropVolume", "swUnitsMassPropDecimalPlaces",
    "swUnitsForce", "swUnitsEnergyUnits", "swUnitsPowerUnits", "swUnitsTimeUnits",
)


def checked(root, name, expected):
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "unit packet path escapes its root")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root)
            and digest(path) == expected, f"unit packet custody differs for {name}")
    return path


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(root, path.name, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and job["control_sha256"] == CONTROL and job["writer_outputs"] == 0
            and job["hidden_inputs_read"] == 0, "unit packet scope differs")
    require(set(job["tools_sha256"]) == TOOLS and Path(__file__).resolve().parent == root / "Tools",
            "unit author must run from its immutable tool closure")
    for name, sha in job["tools_sha256"].items():
        checked(root, Path("Tools") / name, sha)
    seed = checked(root, "Control.SLDPRT", CONTROL)
    api = json.loads(checked(root, "DocumentUnitApi.json", job["api_sha256"]).read_bytes())
    cases = job["cases"]
    require(tuple(case["kind"] for case in cases) == ("corner", "center"),
            "unit source cohort must include two independently dimensioned types")
    require(len({(row["width_m"], row["height_m"], row["depth_m"]) for row in cases}) == 2,
            "unit source designs must differ")
    for case in cases:
        require(set(case) == {"kind", "width_m", "height_m", "depth_m"}
                and all(type(case[key]) is float and 0.001 < case[key] < 0.2
                        for key in ("width_m", "height_m", "depth_m")), "unit source profile differs")
    return root, job, seed, api


def unit_state(author, api):
    enums = api["enums"]
    prefs = enums["swUserPreferenceIntegerValue_e"]
    option = enums["swUserPreferenceOption_e"]["swDetailingNoOptionSpecified"]
    extension = author.typed(author.get(author.model, "Extension"), "ModelDocExtension")
    state = {
        name: int(author.get(extension, "GetUserPreferenceInteger", prefs[name], option))
        for name in PREFERENCES
    }
    state["document_units"] = tuple(author.get(author.model, "GetUnits"))
    for role, value in enums["swUserUnitsType_e"].items():
        unit = author.typed(author.get(author.model, "GetUserUnit", value), "UserUnit")
        state[role] = {"type": int(author.get(unit, "SpecificUnitType")),
                       "conversion": float(author.get(unit, "GetConversionFactor")),
                       "display": str(author.get(unit, "GetUnitsString", True))}
    return state


def set_mode(author, api, mode):
    enums = api["enums"]
    prefs = enums["swUserPreferenceIntegerValue_e"]
    option = enums["swUserPreferenceOption_e"]["swDetailingNoOptionSpecified"]
    extension = author.typed(author.get(author.model, "Extension"), "ModelDocExtension")
    systems = enums["swUnitSystem_e"]
    mass = enums["swUnitsMassPropMass_e"]
    expected = {
        "swUnitSystem": systems["swUnitSystem_MMGS" if mode == MODES[0] else "swUnitSystem_Custom"],
        "swUnitsLinear": enums["swLengthUnit_e"]["swMM"],
        "swUnitsAngular": enums["swAngleUnit_e"]["swDEGREES"],
        "swUnitsMassPropMass": mass["swUnitsMassPropMass_Kilograms" if mode == MODES[2] else "swUnitsMassPropMass_Grams"],
    }
    for name in expected if mode != MODES[0] else ("swUnitSystem",):
        require(author.get(extension, "SetUserPreferenceInteger", prefs[name], option, expected[name]) is True,
                f"native unit setter refused {name} for {mode}")
    observed = unit_state(author, api)
    require(all(observed[key] == value for key, value in expected.items()), "native unit setters did not keep the desired units")
    return observed


def state(author, api, case):
    units = unit_state(author, api)
    model = author.snapshot(case, "Original")
    return {"units": units, "model": model}


def phase(directory, api, case, source=None, expected=None):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(directory / "Record.json", {"case": case["kind"], "authoring": source is None})
    result = {"passed": False, "states": {}, "identity": None}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("guard fresh document unit session", Swapp.sweep)
            controller = recorder.call("start document unit oracle", Swapp.Sw)
            identity = recorder.call("bind exact document unit executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE
                    and controller.revision == "34.5.2", "unexpected document unit oracle build")
            result["identity"] = identity
            author = RectangleAuthor(controller.app, recorder, Swapp)
            if source is None:
                author.build(controller, case)
                base = None
                for mode in MODES:
                    chosen = set_mode(author, api, mode)
                    observed = state(author, api, case)
                    require(observed["units"] == chosen, "native rebuild changed the selected unit preferences")
                    if base is not None:
                        require(observed["model"]["tree"] == base["tree"] and observed["model"]["dimensions_m"] == base["dimensions_m"],
                                "unit selection altered the modeled feature or driver")
                    else:
                        base = observed["model"]
                    target = directory / (mode + ".SLDPRT")
                    require(not target.exists(), "unit source target already exists")
                    author.get(author.model, "SetSaveFlag")
                    saved = recorder.call("save independent native unit state", controller.save_as, author.model, target)
                    require(saved == (True, 0, 0) and target.is_file() and target.stat().st_size > 0,
                            "native unit save failed or warned")
                    result["states"][mode] = observed | {"bytes": target.stat().st_size, "sha256": digest(target),
                                                         "save_diagnostics": list(saved)}
                    recorder.data["result"] = result
                    recorder.flush()
            else:
                require(digest(source) == expected["sha256"], "unit source to reopen changed")
                author.model, error, warning = recorder.call("open authored unit state", controller.open, source, read_only=True)
                result["open_diagnostics"] = [error, warning]
                require(author.model is not None and error == warning == 0, "native unit reopen failed or warned")
                require(Path(author.get(author.model, "GetPathName")).samefile(source), "unit observer opened a foreign document")
                observed = state(author, api, case)
                want = expected["units"]
                require(observed["units"] == want and observed["model"]["tree"] == expected["model"]["tree"],
                        "native unit reopen changed its actual unit preferences or feature tree")
                result["states"][source.stem] = observed | {"sha256": digest(source)}
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                        author.model = None
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress, numeric_checks=len(recorder.data["checks"]))
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not recorder.data["cleanup_errors"]
                            and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    return result | {"record_sha256": digest(recorder.path)}


def run(path, expected):
    require(os.name == "nt", "document unit sources require the exact native Windows oracle")
    root, job, seed, api = verify(path, expected)
    require(metadata() == api, "registered document unit API changed after packet preparation")
    output = root / "Inspection"
    output.mkdir(exist_ok=False)
    phases = {}
    result = {"schema": SCHEMA, "packet_sha256": expected, "passed": False, "phases": phases,
              "heldout_inputs_read": 0, "writer_outputs": 0, "qualified_writer": False}

    def add(role, row):
        phases[role] = row
        write_json(output / "Result.json", result)

    try:
        add("ControlBefore", control(output, "ControlBefore", seed))
        if phases["ControlBefore"]["passed"]:
            for case in job["cases"]:
                case_root = output / case["kind"]
                authored = phase(case_root / "Author", api, case)
                add(case["kind"] + "/Author", authored)
                if authored["passed"]:
                    for mode in MODES:
                        source = case_root / "Author" / (mode + ".SLDPRT")
                        snapshot = phase(case_root / ("Reopen" + mode), api, case, source, authored["states"][mode])
                        add(case["kind"] + "/Reopen" + mode, snapshot)
                        require(digest(source) == authored["states"][mode]["sha256"], "native unit source changed during reopen")
    finally:
        add("ControlAfter", control(output, "ControlAfter", seed))
    verify(path, expected)
    identities = [row.get("identity", row.get("oracle_identity")) for row in phases.values()]
    distinct = {(row["process_id"], row["process_creation_filetime"]) for row in identities if row is not None}
    result["controls_healthy"] = all(phases[role]["passed"] for role in ("ControlBefore", "ControlAfter"))
    result["distinct_native_processes"] = len(distinct)
    result["passed"] = len(distinct) == len(phases) == 10 and all(row["passed"] for row in phases.values())
    write_json(output / "Result.json", result)
    return result


def main():
    parser = ArgumentParser(description="Author independent unit states before the generative unit writer")
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.action == "verify":
        root, _, _, _ = verify(args.packet, args.packet_sha256)
        require(not (root / "Inspection").exists(), "unit source output root is already in use")
        print(json.dumps({"passed": True, "processes_started": 0, "writer_outputs": 0}))
        return 0
    result = run(args.packet, args.packet_sha256)
    print(json.dumps({"passed": result["passed"], "processes": result["distinct_native_processes"]}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
