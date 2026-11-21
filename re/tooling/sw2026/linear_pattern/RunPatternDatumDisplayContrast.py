from argparse import ArgumentParser
from importlib import import_module
from math import dist, isfinite
from pathlib import Path, PureWindowsPath
import json
import os

from AuthorCurves import Recorder, require, write_json
from InspectSdkBlindPart import snapshot, verify_state
from PatternEnvelopePacket import BUILD, CONTROL, ORACLE, checked, digest


SCHEMA = "kit.sw2026.principal-datum-display-contrast.v1"
PART = "KitDatumDisplayProbe.SLDPRT"
TRIAL = "PatternDatumDisplay02"
NATIVE_ROOT = PureWindowsPath(r"C:\KitPatternDatumDisplay01")
ARMS = ("plain", "sized")
BOUND = 5e-9


def verify(packet, pin):
    manifest = json.loads(checked(packet / "Trial.json", pin))
    require(manifest["schema"] == SCHEMA and manifest["native_build"] == BUILD and manifest["oracle_sha256"] == ORACLE
            and manifest["native_locator"] == str(NATIVE_ROOT / PART) and manifest["native_acceptance"] is False,
            "incompatible principal display experiment")
    files = manifest["files"]
    declared = {row["path"] for row in files}
    require(len(declared) == len(files) and declared | {"Trial.json"} == {
        path.relative_to(packet).as_posix() for path in packet.rglob("*") if path.is_file()
    }, "unexpected principal display packet inventory")
    for row in files:
        path = packet / row["path"]
        require(path.resolve().is_relative_to(packet.resolve()) and not path.is_symlink(), "packet file escaped")
        checked(path, row["sha256"], row["bytes"])
    require({row["name"] for row in manifest["arms"]} == set(ARMS)
            and len({row["sha256"] for row in manifest["arms"]}) == len(ARMS), "expected two distinct generated arms")
    for arm in manifest["arms"]:
        require(arm["name"] in ARMS, "unexpected presentation treatment")
        checked(packet / (arm["name"] + ".SLDPRT"), arm["sha256"], arm["bytes"])
    checked(packet / "Control.SLDPRT", CONTROL)
    return manifest


def actual_diagonal(author, typed, bindings, name):
    import Swapp

    def getter(interface, receiver):
        binding = bindings[interface]
        return author.rec.call("declared " + interface + "." + binding["property"], receiver._oleobj_.Invoke,
                               binding["dispid"], 0, binding["invoke"], True, parameters=binding)

    feature = author.get(author.model, "FeatureByName", name)
    require(feature is not None and author.get(feature, "GetTypeName2") == "RefPlane", "expected actual system datum " + name)
    plane = typed.declared_interface(author.get(feature, "GetSpecificFeature2"), "IRefPlane")
    corners = getter("IRefPlane", plane)
    require(isinstance(corners, (list, tuple)) and len(corners) == 2, "expected actual principal plane diagonal " + name)
    result = []
    for corner in corners:
        receiver = typed.declared_interface(Swapp.wc.Dispatch(corner), "IMathPoint")
        value = getter("IMathPoint", receiver)
        require(isinstance(value, (list, tuple)) and len(value) == 3 and all(isinstance(x, (int, float)) and isfinite(x) for x in value),
                "principal plane diagonal is nonfinite")
        result.append(list(value))
    return result


def compare_displays(author, typed, bindings, predicted):
    rows = {}
    for name, want in predicted.items():
        actual = actual_diagonal(author, typed, bindings, name)
        error = max(min(dist(point, target) for target in want) for point in actual)
        matches = any(max(dist(actual[0], want[a]), dist(actual[1], want[b])) <= BOUND
                      for a, b in ((0, 2), (2, 0), (1, 3), (3, 1)))
        rows[name] = {"actual_m": actual, "expected_corners_m": want, "nearest_error_m": error, "matches": matches}
    return rows


def phase(output, label, source, artifact, case, api, *, reopen=False):
    import Swapp
    from AuthorCurves import CurveAuthor
    from AuthorObliqueCylinder import ObliqueAuthor
    from OracleIdentity import application_identity

    folder = output / label
    folder.mkdir(exist_ok=False)
    rec = Recorder(folder / "Record.json", {"phase": label, "source": str(source), "sha256": artifact["sha256"]})
    result = {"passed": False, "states": {}, "displays": {}}
    rec.data["result"] = result
    controller = None
    with Swapp.Dismisser() as monitor:
        try:
            require(not Swapp.application_pids(), "expected idle native oracle")
            checked(source, artifact["sha256"], artifact["bytes"])
            controller = rec.call("open fresh exact-build oracle", Swapp.Sw)
            identity = rec.call("bind executable and lifetime", application_identity, controller.app)
            result["identity"] = identity
            require(identity["version_matches"] and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
                    and controller.revision == "34.5.2", "native oracle changed")
            model, errors, warnings = rec.call("open owned immutable input", controller.open, source, read_only=reopen)
            result["open_counts"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "native part failed or warned on open")
            author = CurveAuthor(controller.app, rec, Swapp)
            author.model = model
            require(Path(author.get(model, "GetPathName")).samefile(source), "native part resolved another owned locator")
            typed = ObliqueAuthor(controller.app, rec, Swapp, api["angles"], None)
            typed.model = model

            def state(name, edited):
                variant = "edited" if edited else "initial"
                result["displays"][name] = compare_displays(author, typed, api["bounds"], case["display_corners_m"][variant])
                value = snapshot(author, case)
                verify_state(rec, value, case, case["tree"], edited=edited)
                result["states"][name] = value
                rec.flush()

            state("first_open", reopen)
            require(author.get(model, "ForceRebuild3", False), "principal contrast rebuild failed")
            state("rebuilt", reopen)
            if not reopen:
                parameter = author.get(model, "Parameter", case["edit"]["dimension"])
                status = int(author.get(parameter, "SetSystemValue3", case["edit"]["new_depth_m"], 1, Swapp.nothing()))
                require(status == 0 and author.get(model, "ForceRebuild3", False), "principal contrast depth edit did not rebuild")
                state("edited", True)
                target = folder / "Edited.SLDPRT"
                require(not target.exists(), "principal contrast output exists")
                save = rec.call("save owned edited derivative", controller.save_as, model, target)
                require(save == (True, 0, 0) and target.is_file() and Path(author.get(model, "GetPathName")).samefile(target),
                        "principal contrast save failed or warned")
                result["saved"] = {"sha256": digest(target.read_bytes()), "bytes": target.stat().st_size}
            require(result["states"]["first_open"]["tree"] == result["states"]["rebuilt"]["tree"]
                    and (reopen or result["states"]["first_open"]["tree"] == result["states"]["edited"]["tree"]),
                    "complete feature owners changed across rebuild or edit")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    checked(source, artifact["sha256"], artifact["bytes"])
    result["passed"] = bool(result["passed"] and not monitor.log and not Swapp.application_pids()
                            and not rec.data["cleanup_errors"] and not result.get("controller_diagnostics"))
    rec.data.update(passed=result["passed"], dialogs=monitor.log)
    rec.flush()
    return result | {"record_sha256": digest(rec.path.read_bytes())}


def run(packet, pin, manifest):
    require(os.name == "nt" and Path(__file__).resolve() == packet / "Tools" / Path(__file__).name,
            "principal display observation belongs to its frozen guest packet")
    from AuthorLinearPatternSources import control_phase
    from AuthorPatternDatumHeight import bounds_metadata
    from ObliqueCylinderApi import metadata

    sw = import_module("Swapp")
    require(not sw.application_pids(), "native entry requires exclusive oracle ownership")
    angles = metadata()
    api = {"angles": angles, "bounds": bounds_metadata(angles)}
    require(not sw.application_pids(), "registered API preflight launched CAD")
    case = json.loads((packet / "Case.json").read_bytes())
    work = Path(NATIVE_ROOT)
    work.mkdir(exist_ok=False)
    working = work / PART
    output = packet.parent / "DisclosedTrial"
    output.mkdir(exist_ok=False)
    control = packet / "Control.SLDPRT"
    report = {"schema": SCHEMA, "trial_sha256": pin, "controls": {}, "phases": {}, "passed": False,
              "private_inputs_read": 0, "registered_metadata": api}
    identities = []

    def bracket(side):
        row, observed = control_phase(control, CONTROL, output / ("Control-" + side + ".json"))
        report["controls"][side] = row
        if observed is not None:
            identities.append(observed)
        return row["passed"]

    try:
        if bracket("before"):
            for arm in manifest["arms"]:
                name = arm["name"]
                raw = checked(packet / (name + ".SLDPRT"), arm["sha256"], arm["bytes"])
                with working.open("xb") as out:
                    out.write(raw)
                changed = phase(output, name + "-edit", working, arm, case, api)
                report["phases"][name + "-edit"] = changed
                checked(working, arm["sha256"], arm["bytes"])
                working.rename(work / (name + "-immutable.SLDPRT"))
                if not changed["passed"]:
                    continue
                identities.append(changed["identity"]["process_creation_filetime"])
                derivative = output / (name + "-edit") / "Edited.SLDPRT"
                restored = phase(output, name + "-reopen", derivative, changed["saved"], case, api, reopen=True)
                report["phases"][name + "-reopen"] = restored
                if restored["passed"]:
                    identities.append(restored["identity"]["process_creation_filetime"])
                write_json(output / "Result.json", report)
    finally:
        if not sw.application_pids():
            bracket("after")
        report["distinct_processes"] = len(set(identities))
        report["passed"] = (len(report["controls"]) == 2 and all(row["passed"] for row in report["controls"].values())
                            and len(report["phases"]) == 4 and all(row["passed"] for row in report["phases"].values())
                            and identities == sorted(set(identities)) and len(identities) == 6)
        if report["passed"]:
            report["presentation_matches"] = {phase_name: {stage: all(row["matches"] for row in states.values())
                                                            for stage, states in value["displays"].items()}
                                              for phase_name, value in report["phases"].items()}
            report["sized_visible_before_rebuild"] = report["presentation_matches"]["sized-edit"]["first_open"]
        verify(packet, pin)
        write_json(output / "Result.json", report)
    return int(not report["passed"])


def main():
    parser = ArgumentParser()
    parser.add_argument("--pin", required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    packet = Path(__file__).resolve().parents[1]
    manifest = verify(packet, args.pin)
    if not args.verify:
        raise SystemExit(run(packet, args.pin, manifest))
    print(json.dumps({"trial_sha256": args.pin, "verified": True, "native_processes": 0}))


if __name__ == "__main__":
    main()
