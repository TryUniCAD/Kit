from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import gcd, isclose, isfinite
import os
from pathlib import Path
import re

LOCK = "5c76de6b79b24044748defa6016dcde7cca928d5391e81a39df59de8e5fe31f1"
CONTROL = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SLOTS = ("Slot01", "Slot02")
ROLES = {"writer_manifest", "writer_verification", "neutral_mapper", "explicit_options", "runtime_guard", "native_observer_manifest"}


def require(value, label):
    if not value:
        raise ValueError(label)


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(row):
    path = Path(row["path"])
    require(path.is_absolute() and not path.is_symlink(), "absolute ordinary file required")
    raw = path.read_bytes()
    require(digest(raw) == row["sha256"], "pinned file changed")
    return raw


def load(row):
    return json.loads(pinned(row))


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return digest(path.read_bytes())


def binding(path, expected):
    value = load({"path": str(path), "sha256": expected})
    require(value["schema"] == "kit.sw2026.blank-drawing-method-binding.v1", "wrong method binding")
    require(value["comparator_sha256"] == digest(Path(__file__).read_bytes()), "comparator changed")
    require(value["source_lock"]["sha256"] == LOCK, "wrong original source lock")
    locked = load(value["source_lock"])
    require(locked["guest_only_private_intent"] and locked["public_promotion_source_lock"], "source custody differs")
    require(locked["internal_constructor_predates_lock"] is True, "constructor chronology changed")
    require(set(locked["slots"]) == set(SLOTS), "source slot inventory changed")
    require(type(value["writer_epoch"]) is int, "explicit integral writer epoch required")
    require(value["private_intent_reads_before_binding"] == value["native_payload_reads_before_generation"] == 0, "access order not qualified")
    require(set(value["artifacts"]) == ROLES, "incomplete writer and observer closure")
    for item in value["artifacts"].values():
        pinned(item)
    verification = load(value["artifacts"]["writer_verification"])
    require(verification["passed"] is True and verification["all_manifest_entries_verified"] is True, "writer closure not independently verified")
    require(verification["writer_manifest_sha256"] == value["artifacts"]["writer_manifest"]["sha256"], "writer verification belongs to another closure")
    return value, locked


def tree(name):
    return [
        ["Comments", "CommentsFolder", None],
        ["Blocks", "BlockFolder", None],
        ["Design Binder", "DocsFolder", None],
        ["Annotations", "DetailCabinet", None],
        ["Markups", "InkMarkupFolder", None],
        ["eDrawings Markups", "MarkupCommentFolder", None],
        [name, "DrSheet", None],
        ["Plane1", "RefPlane", name],
        ["Sketch1", "ProfileFeature", name],
        ["Detail Folder1", "DetailFolder", name],
    ]


def snapshot(name, ratio, width, height):
    return {"sheet": name, "sheet_properties": [0, 13, *ratio, 0, width, height, 1], "view": None, "whats_wrong": 0}


def predict(intent, slot, bound):
    require(set(intent) == {"schema", "slot", "sheet_id", "sheet_name", "width_m", "height_m", "scale_ratio", "edit_scale_ratio", "views", "model_refs", "custody_nonce"}, "extra or missing intent owner")
    require(intent["schema"] == "kit.sw2026.blank-drawing-private-intent.v1" and intent["slot"] == slot and intent["sheet_id"] == "sheet-1", "wrong released intent")
    require(re.fullmatch(r"PrivateSheet[0-9a-f]{16}", intent["sheet_name"]) and re.fullmatch(r"[0-9a-f]{32}", intent["custody_nonce"]), "original private vocabulary changed")
    require(intent["views"] == intent["model_refs"] == [], "blank intent has a model owner")
    require(intent["width_m"] == 11 * 0.0254 and intent["height_m"] == 8.5 * 0.0254, "unsupported paper intent")
    for name in ("scale_ratio", "edit_scale_ratio"):
        terms = intent[name]
        require(type(terms) is list and len(terms) == 2 and all(type(term) is int and 2 <= term <= 47 for term in terms) and gcd(*terms) == 1, "unsupported original scale terms")
    require((intent["scale_ratio"][0] > intent["scale_ratio"][1]) == (slot == "Slot02"), "original scale direction changed")
    require((intent["edit_scale_ratio"][0] > intent["edit_scale_ratio"][1]) != (slot == "Slot02"), "independent edit direction changed")
    common = (intent["width_m"], intent["height_m"])
    return {"schema": "kit.sw2026.blank-drawing-prediction.v1", "slot": slot, "method_binding_sha256": bound, "initial": snapshot(intent["sheet_name"], intent["scale_ratio"], *common), "edited": snapshot(intent["sheet_name"], intent["edit_scale_ratio"], *common), "tree": tree(intent["sheet_name"]), "full_source_semantics_qualified": False}


def same_snapshot(actual, expected):
    require(set(actual) == set(expected), "uncompared native snapshot owner")
    require(actual["sheet"] == expected["sheet"] and actual["view"] is None and type(actual["whats_wrong"]) is int and actual["whats_wrong"] == 0, "native sheet, view or warning state differs")
    values = actual["sheet_properties"]
    require(type(values) is list and len(values) == 8, "native sheet property count differs")
    for index, (value, target) in enumerate(zip(values, expected["sheet_properties"], strict=True)):
        require(type(value) in (int, float) and isfinite(value), "nonfinite native sheet property")
        require(isclose(value, target, rel_tol=0, abs_tol=1e-12) if index in (5, 6) else value == target, "native sheet property differs")


def phase(row, wanted, features, edited, births, intervals):
    record = load(row["record"])
    require(record["passed"] is True and record["first_failure"] is None and record["cleanup_errors"] == [], "native phase or cleanup failed")
    result = record["result"]
    require(result["passed"] is True and result["source_immutable"] is True and result["open_errors"] == result["open_warnings"] == 0, "native source or open state failed")
    require(result["dialogs"] == [] and result["controller_diagnostics"] == [], "native session diagnostics")
    identity = result["oracle_identity"]
    require(identity["version_matches"] is True and identity["file_version"] == "34.5.2.0604" and identity["sha256"] == ORACLE, "wrong native oracle")
    birth = identity["process_creation_filetime"]
    require(type(birth) is int and birth not in births, "native process was reused")
    births.add(birth)
    start, finish = record["started_at"], record["finished_at"]
    require(isfinite(start) and isfinite(finish) and start < finish and (not intervals or intervals[-1][1] <= start), "native phase order or interval differs")
    intervals.append((start, finish))
    require(result["tree"] == features, "complete ordered native tree differs")
    same_snapshot(result["initial"], wanted)
    same_snapshot(result["rebuilt"], wanted)
    if edited is not None:
        same_snapshot(result["edited"], edited)
        require(result["save_status"] == [True, 0, 0] and re.fullmatch(r"[0-9a-f]{64}", result["derivative_sha256"]), "native edited save failed")
    else:
        require("edited" not in result and "save_status" not in result, "fresh reopen performed an unplanned edit")
    return result


def compare(args, locked, bound):
    generation = load({"path": str(args.generation), "sha256": args.generation_sha256})
    require(generation["schema"] == "kit.sw2026.blank-drawing-generation-freeze.v1" and generation["method_binding_sha256"] == args.binding_sha256, "wrong generation freeze")
    require(generation["native_payload_reads"] == 0 and generation["all_outputs_frozen_before_native_attach"] is True, "generation access order differs")
    require(list(generation["slots"]) == list(SLOTS), "both generated slots must freeze together")
    predictions = {}
    outputs = {}
    for slot in SLOTS:
        item = generation["slots"][slot]
        require(item["intent_sha256"] == locked["slots"][slot]["intent_sha256"], "generation intent changed")
        predictions[slot] = load(item["prediction"])
        require(predictions[slot]["schema"] == "kit.sw2026.blank-drawing-prediction.v1" and predictions[slot]["slot"] == slot and predictions[slot]["method_binding_sha256"] == args.binding_sha256 and predictions[slot]["intent_sha256"] == item["intent_sha256"], "prediction identity differs")
        require([build["route"] for build in item["builds"]] == ["extension", "solidworks.slddrw"], "ordinary public write routes differ")
        payloads, targets = [], []
        for build in item["builds"]:
            require(build["writer_epoch"] == bound["writer_epoch"] and build["explicit_options_sha256"] == bound["artifacts"]["explicit_options"]["sha256"] and build["writer_manifest_sha256"] == bound["artifacts"]["writer_manifest"]["sha256"], "writer settings or closure changed")
            require(type(build["target_path"]) is str and bool(build["target_path"]), "explicit output identity required")
            targets.append(build["target_path"])
            require(build["data_file_reads"] == build["native_template_reads"] == build["cad_runtime_calls"] == 0 and build["dropped"] == [], "guarded writer used external data or dropped intent")
            require(build["atomic_write_verified"] is True and build["no_overwrite_verified"] is True, "normal file write behavior not verified")
            payloads.append(pinned(build["output"]))
        require(len(payloads) == 2 and len(set(targets)) == 1 and payloads[0] and payloads[0] == payloads[1], "independent matching-path write outputs differ")
        outputs[slot] = digest(payloads[0])
    observations = load({"path": str(args.observations), "sha256": args.observations_sha256})
    require(observations["schema"] == "kit.sw2026.blank-drawing-native-observations.v1" and observations["generation_sha256"] == args.generation_sha256 and observations["inputs_immutable"] is True, "wrong or mutable native observation deck")
    rows = observations["phases"]
    bases = ["ControlBefore", "Slot01/Source", "Slot01/Generated", "Slot02/Source", "Slot02/Generated", "ControlAfter"]
    require([row["name"] for row in rows] == [base + "/" + stage for base in bases for stage in ("OpenEditSave", "FreshReopen")], "native phase sequence differs")
    control = {"initial": snapshot("Sheet1", [1, 1], 11 * 0.0254, 8.5 * 0.0254), "edited": snapshot("Sheet1", [3, 2], 11 * 0.0254, 8.5 * 0.0254), "tree": tree("Sheet1")}
    births, intervals = set(), []
    for index, base in enumerate(bases):
        slot = base.split("/")[0]
        wanted = predictions[slot] if slot in SLOTS else control
        input_hash = CONTROL if slot not in SLOTS else locked["slots"][slot]["source_sha256"] if base.endswith("/Source") else outputs[slot]
        first, second = rows[2 * index:2 * index + 2]
        require(first["input_sha256"] == input_hash, "native input identity differs")
        saved = phase(first, wanted["initial"], wanted["tree"], wanted["edited"], births, intervals)
        require(second["input_sha256"] == saved["derivative_sha256"], "fresh reopen uses another saved derivative")
        phase(second, wanted["edited"], wanted["tree"], None, births, intervals)
    require(len(births) == 12, "twelve distinct native processes required")
    return {"schema": "kit.sw2026.blank-drawing-comparison.v1", "sheet_lifecycle_passed": True, "distinct_native_processes": len(births), "healthy_control_lifecycles": 2, "compared_sheet_states": 30, "ordered_tree_rows": 120, "source_lock_sha256": LOCK, "method_binding_sha256": args.binding_sha256, "generation_sha256": args.generation_sha256, "observations_sha256": args.observations_sha256, "full_source_semantics_qualified": False, "public_writer_acceptance_claim": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("predict", "compare"))
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--intent", type=Path)
    parser.add_argument("--slot", choices=SLOTS)
    parser.add_argument("--generation", type=Path)
    parser.add_argument("--generation-sha256")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--observations-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        bound, locked = binding(args.binding, args.binding_sha256)
        if args.mode == "predict":
            require(os.name == "nt", "original neutral intents remain guest-private")
            require(args.slot in SLOTS and args.intent is not None, "released intent and slot required")
            row = {"path": str(args.intent), "sha256": locked["slots"][args.slot]["intent_sha256"]}
            value = {**predict(load(row), args.slot, args.binding_sha256), "intent_sha256": row["sha256"]}
        else:
            value = compare(args, locked, bound)
        expected = write_new(args.output, value)
        print(json.dumps({"passed": True, "output_sha256": expected, "private_values_printed": False, "native_launches": 0}))
        return 0
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "private_values_printed": False, "native_launches": 0}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
