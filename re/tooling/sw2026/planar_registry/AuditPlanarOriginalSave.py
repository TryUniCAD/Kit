from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from PlanarRegistryBuild import bind, require
from PlanarRendererNativeSpec import TRIALS, source


ORIGINAL = "d4bd76cdb3a4471f3a0dcabe21a90304032e3e40e25f77cc7d898426e790de98"
GENERATED = "c929e24d886e20ffefa959af57f7c2bb0baf76c6864b02c1878be18571c7bb1f"
SCHEMA = "kit.sw2026.planar-original-renderer-save-comparison.v1"
PREFIX = "visStateKeyData_c/comps/0/comp/moContextChainComponent_c/"
NAME_FIELD = PREFIX + "f20/moReferenceChain_c/f08/moExtFeatureList_c/f08/0/o/moExtFeature_c/f10/h10/moCStringHandle_c/f08"


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    require(not path.is_symlink() and path.is_file(), "owned disclosed input must be a physical file")
    raw = path.read_bytes()
    require(digest(raw) == expected, "disclosed input is not the exact measured snapshot")
    return raw


def project_parent(archive, registry):
    from PlanarVisualOwners import key_data, node
    from para.concentric.AuditConcentricDisplayState import model_inputs
    from para.concentric.ProveVisualStateStore import replay

    refs, config, *_ = model_inputs(archive)
    result, replay_info = replay(archive, registry)
    rows = []
    for entry in key_data(result, config, "Display State-1")["comps"]:
        context = node(entry["comp"], "moContextChainComponent_c")
        chain = node(context["f20"], "moReferenceChain_c")
        group = node(chain["f08"], "moExtFeatureList_c")
        (target,) = group["f08"]
        member = node(target["o"], "moExtFeature_c")
        live = refs[member["f44"]].FieldsValue
        link = node(context["f40"], "moExtObject_c")
        rows.append([member["f44"], context["f30"], live["f3f0"], link["f58"]])
    require(tuple(row[0] for row in rows) == tuple(refs)[::-1], "actual occurrence bindings crossed")
    return rows, replay_info, result.head["root"]


def audit_parent(prior, saved, registry, expected, basename):
    from para.concentric.AuditConcentricDisplayState import compare_typed

    (first, left, old), (last, right, new) = (project_parent(value, registry) for value in (prior, saved))
    count = len(expected["occurrence_rows_in_wire_order"])
    ids = [row[0] for row in expected["occurrence_rows_in_wire_order"]]
    require(first == [[key, 203, 102, 0] for key in ids] and last == [[key, 101, 102, 8] for key in ids],
            "native original save and generated save disagree on the joined occurrence contexts")
    wanted = expected["typed_context_deltas"] | {NAME_FIELD: ["Assem1", basename]}
    delta, split = compare_typed(old, new)
    reverse, joined = compare_typed(new, old)
    require(delta == wanted and reverse == {key: value[::-1] for key, value in wanted.items()}
            and len(split) == 1 and not joined and right["terminal_map"] == left["terminal_map"] + 1
            and count in (2, 3), "relocated native original has unclassified parent visual changes")
    ((shared, parts),) = split.items()
    require(shared.ClassValue.NameValue == "moCStringHandle_c" and shared.FieldsValue["f08"] == "Assem1"
            and len(parts) == 2 and all(value.ClassValue.NameValue == "moCStringHandle_c" for value in parts)
            and {value.FieldsValue["f08"] for value in parts} == {"Assem1", basename},
            "the extra map slot is not the actual detached native document name")
    return {"before": first, "saved": last, "typed_save_fields_match_generated": True,
            "archive_map_counters": [left["terminal_map"], right["terminal_map"]],
            "visual_stream_hashes": [left["sha256"], right["sha256"]],
            "extra_model_name_owner": {"retained_name": "Assem1", "saved_name": basename},
            "unclassified_parent_changes": 0}


def audit_child(prior, saved, registry, expected, measured):
    from PlanarRendererInput import differences, material_id, observe_looks

    first, last = (observe_looks(value, registry) for value in (prior, saved))
    delta = [after - before for before, after in zip(*(tuple(map(material_id, row[0])) for row in (first, last)), strict=True)]
    generated = [after - before for before, after in zip(expected["frozen_ids"], expected["saved_ids"], strict=True)]
    cursors = [value[1].AppearanceValue.NextAppearanceId for value in (first, last)]
    fields = [list(differences(a, b)) for a, b in zip(first[0], last[0], strict=True)]
    require(delta == generated == [3, 3, 0] and cursors[1] - cursors[0] == 3
            and fields == [["f20.f90.f00"], ["f20.f90.f00"], []]
            and first[2]["sha256"] == last[2]["sha256"] and expected["child_visualstates_unchanged"]
            and all(value[2]["physical_density_parameter"] == [1000.0, 0]
                    and value[2]["active_configuration_density"] == -1.0 for value in (first, last)),
            "named appearance allocation or default physical density differs")
    require([list(map(material_id, value[0])) for value in (first, last)]
            == [measured[key]["appearance_ids"] for key in ("original_roles", "resaved_roles")],
            "host reading disagrees with the native resave receipt")
    return {"live_and_detached_appearance_id_deltas": delta, "definition_cursor": cursors,
            "renderer_field_paths": fields, "visual_stream_sha256": first[2]["sha256"],
            "visual_stream_identical": True, "native_density_unchanged": [1000.0, 0]}


def case(share, resave, slot):
    bind(ROOT)
    from para.concentric.ProveVisualStateStore import registry
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    result = json.loads(checked(resave / "Receipt.json", ORIGINAL))
    prior = json.loads(checked(ROOT / "re/solidworks/measurements/2026/PlanarRendererSavedRead01.json", GENERATED))
    require(result["passed"] and result["controls_match"] and result["originals_unchanged"]
            and result["native_processes"] == 8 and result["numeric_checks"] == 642 and result["rebind_closed_copy"]
            and prior["original_native_mechanics_passed"] and prior["post_save_comparison_complete"]
            and prior["original_aggregate_passed"] is False,
            "both separately measured native batches and their immutable results are required")
    source_paths, evidence, _ = source(share, slot)
    row = result["cases"][slot]
    require(row["passed"] and row["ordered_tree_matches"] and row["mechanics_match"] and row["preserves_effective_density"],
            "the original resave did not independently establish native parity")
    source_data, saved_data = {}, {}
    for owner in ("parent", "child"):
        incoming = source_paths[owner]
        saved = resave / slot / incoming.name
        source_data[owner] = SldprtArchive.from_bytes(checked(incoming, evidence[owner + "_sha256"]), incoming.name)
        saved_data[owner] = SldprtArchive.from_bytes(checked(saved, row["saved_" + owner + "_sha256"]), saved.name)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "offline typed observation acquired a native runtime")
    observed = prior["cases"][slot]
    reg = registry()
    return {"parent": audit_parent(source_data["parent"], saved_data["parent"], reg, observed["parent"], source_paths["parent"].stem),
            "child": audit_child(source_data["child"], saved_data["child"], reg, observed["child"], row),
            "saved_native_hashes": {key: row["saved_" + key + "_sha256"] for key in ("parent", "child")}}


def supervise(share, resave, output):
    require(resave.parent == share and not output.exists(), "use exact external capture siblings and a fresh receipt")
    info = {}
    for slot in TRIALS:
        worker = run((sys.executable, "-I", "-B", str(HERE), str(share), str(resave), "--slot", slot),
                     capture_output=True, timeout=100)
        require(worker.returncode == 0, slot + " typed observation failed: " + worker.stderr.decode(errors="replace"))
        require(not worker.stderr, "typed offline observation emitted a diagnostic")
        info[slot] = json.loads(worker.stdout)
    evidence = {"schema": SCHEMA, "passed": True, "native_resave_sha256": ORIGINAL, "known_generated_read_sha256": GENERATED,
                "worker_count": len(info), "native_processes_started": 0, "new_writer_outputs": 0,
                "new_heldout_credit": 0, "original_combined_receipt_passed": False, "cases": info}
    raw = (json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with output.open("xb") as file:
        file.write(raw)
    return {"passed": True, "receipt_sha256": digest(raw)}


if __name__ == "__main__":
    command = ArgumentParser()
    command.add_argument("share", type=Path)
    command.add_argument("resave", type=Path)
    command.add_argument("--slot", choices=TRIALS)
    command.add_argument("--output", type=Path)
    args = command.parse_args()
    if args.slot is None and args.output is None:
        command.error("a fresh --output is required for the two-case audit")
    value = (case(args.share, args.resave, args.slot) if args.slot
             else supervise(args.share, args.resave, args.output))
    print(json.dumps(value, sort_keys=True, allow_nan=False))
