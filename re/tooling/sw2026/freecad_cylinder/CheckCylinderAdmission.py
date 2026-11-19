from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import platform
import subprocess
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected=None):
    require(path.is_file() and not path.is_symlink(), "use an immutable regular disclosed input")
    raw = path.read_bytes()
    require(expected is None or digest(raw) == expected, f"disclosed source changed: {path.name}")
    return raw


def save(path, value):
    raw = encoded(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def run_worker(tool, code, mode, raw, output, extra=()):
    process = subprocess.run([sys.executable, "-I", "-B", str(tool), str(code), mode, *extra],
                             input=raw, capture_output=True, timeout=90)
    with output.open("xb") as stream:
        stream.write(process.stdout)
    require(not process.stderr, "the source process emitted unexpected stderr")
    result = json.loads(process.stdout)
    require(result["generated_writer_outputs"] == result["native_bytes_emitted"] == result["native_processes_started"]
            == result["heldout_inputs_read"] == 0 and result["boundary_events"] == [],
            "source admission crossed its native or file boundary")
    return process.returncode, result, digest(process.stdout)


def mutate(request, name):
    value = deepcopy(request)
    document = value["document"]
    feature = document["feature_timeline"]["$tuple"][0]
    parameters = document["parameters"]["$tuple"]
    by_path = {row["attributes"]["freecad_path"]: row for row in parameters}
    native = feature["definition"]["object_data"]

    def sync_native():
        feature["attributes"]["freecad"] = deepcopy(native)
        document["metadata"]["freecad"]["objects"] = [deepcopy(native)]

    def set_scalar(path, number):
        native["properties"][path]["children"][0]["attributes"]["value"] = str(number)
        by_path[path]["attributes"]["freecad_property"] = deepcopy(native["properties"][path])
        by_path[path]["value"]["value"] = float(number)
        sync_native()

    if name == "missing_radius_parameter":
        parameters.remove(by_path["Radius"])
        feature["parameter_ids"]["$tuple"].remove(by_path["Radius"]["id"])
    elif name == "stale_height_property":
        by_path["Height"]["value"]["value"] *= 1.1
    elif name == "foreign_parameter_owner":
        by_path["Radius"]["owner_id"] = "foreign-feature"
    elif name == "radius_unit_changed":
        by_path["Radius"]["value"]["unit"] = "m"
    elif name == "reordered_parameter_owners":
        parameters.reverse()
        feature["parameter_ids"]["$tuple"].reverse()
    elif name == "feature_label_changed":
        feature["name"] = "Different feature"
    elif name == "metadata_stripped":
        document["metadata"] = {}
    elif name == "copied_native_object":
        document["metadata"]["freecad"]["objects"][0]["object_id"] = "different"
    elif name == "provenance_stripped":
        feature["provenance"] = None
    elif name == "translated_placement":
        native["properties"]["Placement"]["children"][0]["attributes"]["Px"] = "5.0"
        sync_native()
    elif name == "partial_sweep":
        set_scalar("Angle", 270.0)
    elif name == "active_attachment":
        native["properties"]["AttachmentSupport"]["children"][0]["attributes"]["count"] = "1"
        sync_native()
    elif name == "suppressed_primitive":
        feature["suppressed"] = True
    elif name == "shape_payload_stripped":
        document["brep_payloads"]["$tuple"] = [row for row in document["brep_payloads"]["$tuple"] if row["kind"] != "shape"]
    elif name == "brep_radius_changed":
        side, = (row for row in document["brep"]["surfaces"]["$tuple"] if row["$type"] == "CylinderSurface")
        side["radius"] *= 1.1
    elif name == "brep_cap_height_changed":
        caps = [row for row in document["brep"]["surfaces"]["$tuple"] if row["$type"] == "PlaneSurface"]
        max(caps, key=lambda row: row["origin"]["z"])["origin"]["z"] *= 1.1
    elif name == "formula_added":
        by_path["Radius"]["expression"] = {"$type": "Expression", "source": "2.0", "language": "freecad",
                                              "parameter_ids": {"$tuple": []}}
    elif name == "body_caption_changed":
        document["bodies"]["$tuple"][0]["name"] = "Different body"
    else:
        raise ValueError("unknown source boundary mutation")
    return value


def compare_measure(expected, actual):
    wanted = [expected["volume_mm3"] * 1e-9, expected["area_mm2"] * 1e-6,
              *(value * 1e-3 for value in expected["center_mm"])]
    measured = [actual["volume_m3"], actual["area_m2"], *actual["center_of_mass_m"]]
    require(all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
                for left, right in zip(wanted, measured, strict=True)),
            "the independent cylinder prediction differs from the disclosed native measurement")
    require(actual["solid_bodies"] == 1 and actual["rebuild_feature_errors"] == actual["rebuild_feature_warnings"] == 0,
            "a disclosed native companion is not clean")
    return 5


def main():
    parser = ArgumentParser(description="Audit the actual disclosed FreeCAD cylinder source envelope and preparation boundary")
    parser.add_argument("code_root", type=Path)
    parser.add_argument("sources", type=Path)
    parser.add_argument("deck", type=Path)
    parser.add_argument("native_receipt", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--code-manifest", type=Path, required=True)
    parser.add_argument("--code-manifest-sha256", required=True)
    args = parser.parse_args()
    code = args.code_root.resolve(strict=True)
    source = args.sources.resolve(strict=True)
    manifest = json.loads(checked(args.code_manifest, args.code_manifest_sha256))
    for name, identity in manifest["files_sha256"].items():
        checked(code / name, identity)
    tool = Path(__file__).resolve().with_name("CylinderIntentProcess.py")
    tools = {name: digest(checked(tool.with_name(name))) for name in (
        "CylinderIntentProcess.py", "CylinderSourceIntent.py", "CorrelateCylinderBrep.py", Path(__file__).name)}
    deck_raw = checked(args.deck)
    deck = json.loads(deck_raw)
    require(deck["passed"] and deck["heldout_inputs_read"] == deck["writer_outputs"] == 0
            and [row["case"] for row in deck["cases"]] == ["CylinderA", "CylinderB"],
            "use only the published two disclosed cylinder source cases")
    args.output.mkdir(exist_ok=False)
    workers = args.output / "Workers"
    workers.mkdir()
    projections = args.output / "CurrentNeutral"
    projections.mkdir()
    predictions = args.output / "Predictions"
    predictions.mkdir()
    requests = args.output / "Requests"
    requests.mkdir()
    records, states, custody = [], {}, []
    for row in deck["cases"]:
        name = row["case"]
        source_raw = checked(source / "Disclosed" / (name + ".FCStd"), row["source_sha256"])
        historical = checked(source / "StrictNeutral02" / (name + ".json"), row["strict_neutral_sha256"])
        radius_factor = row["native_spec"]["edit"]["factor"]
        depth_factor = row["second_independent_edit"]["factor"]
        neutral_path = projections / (name + ".json")
        extra = ("--neutral-output", str(neutral_path), "--radius-edit-factor", str(radius_factor),
                 "--depth-edit-factor", str(depth_factor))
        status, current, identity = run_worker(tool, code, "read", source_raw, workers / (name + "Read.json"), extra)
        require(status == 0 and current["passed"], "the current ordinary strict source read failed")
        records.append({"case": name, "kind": "normal_strict_read", "sha256": identity})
        current_document = json.loads(checked(neutral_path))
        versions = {"historical": json.loads(historical), "current": current_document}
        current_request = None
        for version, document in versions.items():
            request = {"document": document, "radius_edit_factor": radius_factor,
                       "depth_edit_factor": depth_factor, "written_at": 1800000000}
            save(requests / (name + version + ".json"), request)
            status, result, identity = run_worker(tool, code, "intent", encoded(request),
                                                  workers / (name + version + "Intent.json"))
            require(status == 0 and result["passed"] and not result["intent"]["native_construction_admitted"],
                    "the full source intent audit failed or claimed construction admission")
            records.append({"case": name, "kind": version + "_intent", "sha256": identity})
            if version == "current":
                require(result["intent"] == current["intent"] and result["prediction"] == current["prediction"],
                        "strict FCStd and typed current JSON disagree")
                current_request = request
                states[name] = result
                save(predictions / (name + ".json"), result["prediction"])
            else:
                same = ("names", "identities", "parameter_order", "parameters", "placement", "attachment_offset",
                        "predicted_pristine")
                require(all(result["intent"][field] == current["intent"][field] for field in same),
                        "the historical and current strict source semantic owners changed")
        for mode in ("preparation-refusal", "public-refusal"):
            status, result, identity = run_worker(tool, code, mode, encoded(current_request),
                                                  workers / (name + mode + ".json"))
            require(status == 0 and result["passed"], "the existing unqualified preparation boundary did not refuse")
            require(result["refusal"]["type"] == ("ValueError" if mode == "preparation-refusal" else "AdapterNotFoundError"),
                    "an unrelated harness exception was counted as a preparation refusal")
            records.append({"case": name, "kind": mode, "sha256": identity, "refusal": result["refusal"]})
        status, repeat, identity = run_worker(tool, code, "intent", encoded(current_request),
                                             workers / (name + "Repeat.json"))
        require(status == 0 and repeat == states[name], "the repeated source prediction changed")
        records.append({"case": name, "kind": "fresh_repeat", "sha256": identity})
        custody.append({"case": name, "source_sha256": row["source_sha256"],
                        "historical_strict_json_sha256": digest(historical),
                        "current_strict_json_sha256": digest(checked(neutral_path)),
                        "current_source_document_sha256": current["intent"]["full_document_sha256"],
                        "prediction_sha256": digest(checked(predictions / (name + ".json")))})
    prediction_lock = {"schema": "kit.sw2026.freecad-cylinder-prediction-lock.v1", "cases": custody,
                       "native_observations_read": False, "tools_sha256": tools,
                       "code_manifest_sha256": args.code_manifest_sha256, "source_deck_sha256": digest(deck_raw)}
    prediction_lock_sha = save(args.output / "PredictionLock.json", prediction_lock)
    current_request = json.loads(checked(requests / "CylinderAcurrent.json"))
    variants = ("missing_radius_parameter", "stale_height_property", "foreign_parameter_owner", "radius_unit_changed",
                "reordered_parameter_owners", "feature_label_changed", "metadata_stripped", "copied_native_object",
                "provenance_stripped", "translated_placement", "partial_sweep", "active_attachment", "suppressed_primitive",
                "shape_payload_stripped", "brep_radius_changed", "brep_cap_height_changed", "formula_added", "body_caption_changed")

    def negative(name):
        status, result, identity = run_worker(tool, code, "intent", encoded(mutate(current_request, name)),
                                              workers / (name + ".json"))
        require(status == 3 and not result["passed"] and result["error"]["type"] in ("ValueError", "ValidationError"),
                "a malformed source crossed its guarded projection boundary")
        return {"kind": name, "sha256": identity, "refusal": result["error"]}

    with ThreadPoolExecutor(max_workers=4) as pool:
        negatives = list(pool.map(negative, variants))
    native_raw = checked(args.native_receipt)
    native = json.loads(native_raw)
    require(native["passed"] and native["hidden_inputs_read"] == native["generated_writer_output_count"]
            == native["heldout_source_count"] == 0, "the published receipt is not the disclosed native-source cohort")
    comparisons = 0
    for row in native["cases"]:
        predicted = states[row["case"]]["prediction"]
        require(predicted["source_sha256"] == row["freecad_sha256"], "native companion custody differs")
        for measured in row["pristine"].values():
            comparisons += compare_measure(predicted["pristine"], measured)
        comparisons += compare_measure(predicted["independent_radius_edit"], row["radius_edited"])
        comparisons += compare_measure(predicted["independent_depth_edit"], row["depth_edited"])
    require(comparisons == 50, "the source companion measurement inventory changed")
    for row in deck["cases"]:
        checked(source / "Disclosed" / (row["case"] + ".FCStd"), row["source_sha256"])
        checked(source / "StrictNeutral02" / (row["case"] + ".json"), row["strict_neutral_sha256"])
    for name, identity in tools.items():
        checked(tool.with_name(name), identity)
    report = {"schema": "kit.sw2026.freecad-cylinder-admission-audit.v1", "passed": True,
              "code_base_revision": manifest["base_revision"], "code_manifest_sha256": args.code_manifest_sha256,
              "tools_sha256": tools, "runtime": {"implementation": platform.python_implementation(),
                                                   "version": platform.python_version(), "platform": sys.platform},
              "source_deck_sha256": digest(deck_raw), "native_source_receipt_sha256": digest(native_raw),
              "prediction_lock_sha256": prediction_lock_sha, "prediction_locked_before_observation_read": True,
              "cases": [{"case": name, "intent": states[name]["intent"], "custody": next(row for row in custody if row["case"] == name)}
                        for name in states],
              "positive_processes": records, "negative_processes": negatives,
              "independent_source_analytic_comparisons": comparisons, "sdk_processes": len(records) + len(negatives),
              "source_before_after_hashes_unchanged": True, "runtime_native_input_file_reads": 0,
              "code_imports_permitted_only_from_frozen_source_root": True,
              "native_processes_started": 0, "heldout_inputs_read": 0, "generated_writer_outputs": 0,
              "primitive_lowering_implemented": False, "source_equivalence_qualified": False,
              "heldout_source_lock_present": False, "native_construction_admitted": False}
    report_sha = save(args.output / "Result.json", report)
    print(json.dumps({"passed": True, "report_sha256": report_sha, "sdk_processes": report["sdk_processes"],
                      "analytic_comparisons": comparisons, "generated_writer_outputs": 0}))


if __name__ == "__main__":
    main()
