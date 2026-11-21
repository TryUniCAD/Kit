import argparse
from copy import deepcopy
from math import isclose
from pathlib import Path
import json
import re
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from ConcentricNativeContract import ORACLE, ROLES, checked, digest, require, signature, write_json
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from para.concentric.PrepareSignedConcentricNative import check_live_signs, check_saved, stage_case
from para.concentric.ProjectConcentricRadialIntent import light_values, source_scene
from para.concentric.ProveSignedConcentricWriter import inventory_receipt, source_inventory


BASELINE_TRIAL = "8e0feb327fdacd559f9a9a56bcbb24ecf679bb4a40e9bff29f23f3cf7b03ae45"
BASELINE_RESULT = "3c4dfe72c531d8d8b06dcaa3b2acec97da02692a96c120028f32ddca233e502b"
SCHEMA = "kit.sw2026.disclosed-concentric-parent-lights-native.v1"
CONTRAST = {"NameValue": "Directional Intensity Probe", "DiffuseValue": 0.6875,
            "SpecularValue": 0.5625, "ColourValue": 0xC0A060}
NATIVE_TYPES = {"ambient": "AmbientLight", "directional": "DirectionLight"}
STATES = {"ControlBefore": ("initial", "rebuilt"), "Generated": ("initial", "rebuilt", "edited", "saved_state"),
          "Reopen": ("initial", "rebuilt"), "ControlAfter": ("initial", "rebuilt")}


def evidence(root, trial, name):
    locator = "Evidence/" + name + ".json"
    return checked(root / locator, trial["files_sha256"][locator]).read_bytes()


def expect_lights(tree, scene, lights, changed_name=None):
    types = set(NATIVE_TYPES.values())
    actual = [row for row in tree if row[1] in types]
    expected = [[row["NameValue"], NATIVE_TYPES[row["KindValue"]], scene] for row in lights]
    if changed_name is None:
        require(actual == expected, "actual parent light tree differs")
        return expected
    require(sum(row[0] == changed_name for row in actual) == 1, "expected one baseline parent light to rename")
    alternate = [[CONTRAST["NameValue"], *row[1:]] if row[0] == changed_name else row for row in actual]
    require(alternate == expected and alternate != actual, "authored light is not an independent native discriminator")
    return [[CONTRAST["NameValue"], *row[1:]] if row[0] == changed_name and row[1] in types else row for row in tree]


def prepare(base, out, revision, written_at):
    require(re.fullmatch("[0-9a-f]{40}", revision), "provide the exact pinned writer revision")
    trial = json.loads(checked(base / "Trial.json", BASELINE_TRIAL).read_bytes())
    prior = json.loads(checked(base / "Result.json", BASELINE_RESULT).read_bytes())
    require(prior["packet_sha256"] == BASELINE_TRIAL and prior["passed"] and prior["controls_healthy"],
            "the disclosed aligned baseline and both controls must have passed")
    runtime = evidence(base, trial, "GuestPython")
    neutral = json.loads(evidence(base, trial, "Neutral"))
    predicted = json.loads(evidence(base, trial, "Prediction"))
    signed = json.loads(evidence(base, trial, "ExpectedSigned"))
    check_live_signs(prior, signed["generated"], signed["control"])
    original = neutral["lights"]
    require(tuple(row["KindValue"] for row in original) == ("ambient", "directional", "directional", "directional"),
            "the independently measured baseline light family differs")
    scene, = (row[0] for row in predicted["generated"]["tree"] if row[1] == "EnvFolder")
    expect_lights(predicted["control"]["tree"], scene, original)
    altered = deepcopy(original)
    altered[1].update(CONTRAST)
    predicted["generated"]["tree"] = expect_lights(
        predicted["generated"]["tree"], scene, altered, original[1]["NameValue"])
    closure = inventory_receipt(source_inventory(REPO))
    prepared = stage_case(out, base, trial, runtime, trial["controls"], closure,
                          FromData(neutral["document"]), tuple(map(tuple, neutral["local_axes"])),
                          scene, original, predicted, signed["generated"], signed["control"], written_at,
                          "ConcentricParentLights", parent_intents=altered, writer_revision=revision,
                          preparer=Path(__file__))
    require(inventory_receipt(source_inventory(REPO)) == closure, "the pinned writer changed during construction")
    write_json(out / "ParentLightsPreparation.json", prepared)
    return {"trial_sha256": prepared["trial_sha256"], "host_verify_passed": prepared["host_verify_passed"],
            "runtime_io_attempts": prepared["build"]["runtime_io_attempts"]}


def same_value(actual, expected):
    if type(expected) is float:
        return type(actual) in (int, float) and isclose(actual, expected, rel_tol=2e-7, abs_tol=1e-12)
    if type(expected) is list:
        return isinstance(actual, (list, tuple)) and len(actual) == len(expected) and all(
            same_value(left, right) for left, right in zip(actual, expected, strict=True))
    return type(actual) is type(expected) and actual == expected


def inspect_parent(path, checksum, scene, expected):
    archive = SldprtArchive.from_bytes(checked(path, checksum).read_bytes())
    folder, lights = source_scene(ReadNativeLink(archive, 0))
    require(folder == scene and len(lights) == len(expected), "typed parent scene owner differs")
    checked_values = 0
    for light, wanted in zip(lights, expected, strict=True):
        actual = light_values(light)
        require(set(actual) == set(wanted), "parent input domains changed")
        for field, value in wanted.items():
            require(same_value(actual[field], value), "saved typed parent light differs at " + field)
            checked_values += 1
    return checked_values


def postflight(packet, expected):
    root = packet.parent
    trial = json.loads(checked(packet, expected).read_bytes())
    require(trial["case"] == "ConcentricParentLights" and trial["oracle_sha256"] == ORACLE
            and trial["preparer_sha256"] == digest(Path(__file__))
            and trial["source_closure"] == inventory_receipt(source_inventory(REPO)), "unexpected exact scene closure")
    for name, wanted in trial["files_sha256"].items():
        checked(root / name, wanted)
    native_path = root / "Result.json"
    native = json.loads(native_path.read_bytes())
    require(native["packet_sha256"] == expected and not native["heldout_acceptance"], "wrong disclosed native result")
    for role in ROLES:
        path = root / "Inspection" / role / "Record.json"
        if path.is_file():
            record = json.loads(path.read_bytes())
            require(record["job"] == {"phase": role, "packet_sha256": expected}, "wrong phase packet")
            if "result" in record:
                require(native["phases"][role] == record["result"], "phase and aggregate differ")
    native_controls = all(native["phases"][role] and native["phases"][role]["passed"] for role in (ROLES[0], ROLES[-1]))
    if native_controls:
        native_controls = signature(native["phases"][ROLES[0]]["rebuilt"]) == signature(native["phases"][ROLES[-1]]["rebuilt"])
    result = {"schema": SCHEMA, "writer_revision": trial["writer_revision"], "trial_sha256": expected,
              "native_result_sha256": digest(native_path), "oracle_sha256": ORACLE, "oracle_file_version": "34.5.2.0604",
              "passes_full_lifecycle": bool(native["passed"]), "controls_healthy": native_controls,
              "distinct_native_processes": native["distinct_native_processes"], "heldout_acceptance": False,
              "whole_source_admitted": False, "faults": {role: row.get("first_failure") if row else "phase missing"
                                                        for role, row in native["phases"].items() if not row or not row["passed"]}}
    if not native["passed"]:
        return result
    signed = json.loads(evidence(root, trial, "ExpectedSigned"))
    neutral = json.loads(evidence(root, trial, "Neutral"))
    predicted = json.loads(evidence(root, trial, "Prediction"))
    build = json.loads(evidence(root, trial, "Build"))
    scene, lamps = neutral["parent_environment"], neutral["parent_lights"]
    axis_checks = check_live_signs(native, signed["generated"], signed["control"])
    observed_names = 0
    for role, states in STATES.items():
        expected_lamps = neutral["lights"] if role.startswith("Control") else lamps
        for state in states:
            scene_tree = native["phases"][role][state]["tree"]
            observed_names += len(expect_lights([[row["name"], row["type"], row["parent"]] for row in scene_tree],
                                                scene, expected_lamps))
    saved = native["phases"]["Generated"]["saved"]
    hashes = {"parent": saved["parent"], "child": saved["child"]["native_sha256"]}
    paths = {role: root / "Working" / filename for role, filename in trial["working_names"].items()}
    fixed = root / "Frozen" / trial["working_names"]["parent"]
    generated_fields = inspect_parent(fixed, trial["generated_sha256"]["parent"], scene, lamps)
    saved_fields = inspect_parent(paths["parent"], hashes["parent"], scene, lamps)
    check_saved(paths["parent"], paths["child"], hashes, signed["generated"], predicted["generated"])
    result.update(ordered_live_light_observations=observed_names, generated_typed_light_fields=generated_fields,
                  saved_typed_light_fields=saved_fields, live_signed_axis_checks=axis_checks,
                  candidate_numeric_checks=sum(native["phases"][role]["numeric_checks"] for role in ("Generated", "Reopen")),
                  parent_scene_build=build["parent_lighting"], runtime_io_attempts=build["runtime_io_attempts"],
                  native_saved_sha256=hashes, full_geometry_and_mate_lifecycle=True, authored_light=CONTRAST)
    return result


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser("prepare")
    stage.add_argument("baseline", type=Path)
    stage.add_argument("unused_packet", type=Path)
    stage.add_argument("revision")
    stage.add_argument("written_at", type=int)
    after = commands.add_parser("postflight")
    after.add_argument("trial", type=Path)
    after.add_argument("sha256")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.baseline.resolve(), args.unused_packet.resolve(), args.revision, args.written_at)
    else:
        result = postflight(args.trial.resolve(), args.sha256)
        receipt = args.trial.resolve().parent / "ParentLightsPostflight.json"
        require(not receipt.exists(), "preserve the first postflight result")
        write_json(receipt, result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
