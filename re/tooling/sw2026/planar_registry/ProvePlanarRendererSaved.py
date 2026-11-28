from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run as run_process
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarRegistryBuild import ROOT, bind, file_sha, load, require, subtask, write
from PlanarRendererNativeSpec import CHILD, ORACLE, PHASES, SCHEMA, TRIALS, exact


PACKET_SHA256 = "a8776d5de20ee7c691cb088a5bb589944ef0c24bf7e57b908b7d088177be989c"
RESULT_SHA256 = "215f24271caf6c3289cc56ae12f4f8e02b45d98b01329ec61b309a16b7b184e1"
SOURCE_REVISION = "fb3efea12dab0d19dd7cc9a0b37be5d9007f336d"
SOURCE_TREE = "5bb76b33b5faafcb15a2f18289e005ed7e9e157f"
COUNTS = {"A20": 2, "A21": 3}
OWN_FILES = ("PlanarVisualOwners.py", "ReadPlanarRendererNative.py", "PlanarSaveDelta.py", "ProvePlanarRendererSaved.py")
ORACLE_BUILD = "34.5.2.0604"


def inputs(root):
    packet = load(root / "Packet.json", PACKET_SHA256)
    result = load(root / "Inspection" / "Result.json", RESULT_SHA256)
    require(packet["schema"] == result["schema"] == SCHEMA and result["packet_sha256"] == PACKET_SHA256
            and packet["writer_revision"] == result["writer_revision"] and packet["oracle_sha256"] == ORACLE
            and tuple(packet["phases"]) == tuple(result["phases"]) == PHASES
            and set(packet["cases"]) == set(result["cases"]) == set(TRIALS)
            and packet["new_heldout_credit"] == result["new_heldout_credit"] == 0
            and result["public_writer_qualified"] is result["whole_source_admitted"] is False
            and packet["writer_runtime_file_reads"] == 0 and result["passed"] is False,
            "supplement requires the intact disclosed failed aggregate and its frozen inputs")
    require(all(result[k] for k in ("controls_healthy", "control_identity_preserved", "frozen_inputs_unchanged",
                                     "saved_files_unchanged")), "native controls or tied files did not pass")
    phases = result["phases"]
    measured = [row["oracle_identity"]["process_creation_filetime"] for row in phases.values()]
    require(len(set(measured)) == len(measured) == result["native_processes"] == len(PHASES)
            and all(row["passed"] and row["open_errors"] == row["open_warnings"] == 0 and not row["dialogs"]
                    and row["oracle_identity"]["file_version"] == ORACLE_BUILD
                    and row["oracle_identity"]["sha256"] == ORACLE for row in phases.values())
            and sum(row["numeric_checks"] for row in phases.values()) == result["numeric_checks"] == 834,
            "native phase build, control or numerical custody differs")
    return packet, result


def pairs(root, slot, packet, native, request):
    trial = root / slot
    names = {"parent": PureWindowsPath(request["native_parent"]).name, "child": CHILD}
    require(names["parent"].endswith(".SLDASM") and all(Path(name).name == name for name in names.values()),
            "planar renderer packet lost its actual parent and child basenames")
    frozen, working = trial / "FrozenGenerated", trial / "Working"
    require(not trial.is_symlink() and not frozen.is_symlink() and not working.is_symlink(),
            "planar renderer assets require their own exact sibling directories")
    expected = packet["cases"][slot]["generated"]
    observed = native["phases"][slot + "Generated"]["saved"]
    reread = native["phases"][slot + "FreshReopen"]
    require(observed["child"]["original_sha256"] == expected["child"]["sha256"]
            and reread["child_stamp_on_open"] == observed["child"]["update_stamp"]
            and observed["child"]["path_basename"] == CHILD and observed["child"]["save_status"] == [True, 0, 0],
            "the actual child-first native save and reopen custody differs")
    before = {key: {"file": str(exact(frozen / name, expected[key]["sha256"])), "sha256": expected[key]["sha256"]}
              for key, name in names.items()}
    hashes = {"parent": observed["parent"], "child": observed["child"]["native_sha256"]}
    after = {key: {"file": str(exact(working / name, hashes[key])), "sha256": hashes[key]}
             for key, name in names.items()}
    require(all(Path(item["file"]).stat().st_size == expected[key]["bytes"] for key, item in before.items())
            and Path(after["child"]["file"]).stat().st_size == observed["child"]["native_bytes"],
            "frozen or native saved file size differs")
    return before, after, {"saved": observed["child"]["update_stamp"], "open": reread["child_stamp_on_open"],
                           "after_rebuild": reread["child_stamp_after_rebuild"]}


def read_archives(rows):
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    return {role: SldprtArchive.from_bytes(Path(item["file"]).read_bytes(), Path(item["file"]).name)
            for role, item in rows.items()}


def worker(root, slot):
    bind(ROOT)
    from PlanarSaveDelta import PARENT_REFUSAL, child_delta, parent_delta
    from ProvePlanarAssemblyIdentity import excluded_modules
    from ReadPlanarRendererNative import observe
    from RectanglePresentation import differences as label_differences
    from para.concentric.ProveVisualStateStore import registry

    packet, native = inputs(root)
    prospect = packet["cases"][slot]
    previous = native["cases"][slot]
    failed = previous["saved_strict_read"]
    require(previous["native_comparison"]["passed"] and previous["passed"] is failed["passed"] is False
            and not failed["cad_runtime_imports"] and failed["stages"]["saved"] == {"passed": False,
                "error": repr(ValueError(PARENT_REFUSAL))}, "original strict saved refusal or native comparison changed")
    trial = root / slot
    request = load(trial / "NeutralRequest.json", prospect["request_sha256"])
    prediction = load(trial / "Prediction.json", prospect["prediction_sha256"])
    host = load(trial / "StrictHostRead.json", prospect["strict_host_read_sha256"])
    before, after, child_stamps = pairs(root, slot, packet, native, request)
    require(host["passed"] and host["stages"]["generated"]["sha256"] == {key: row["sha256"] for key, row in before.items()},
            "frozen generated controls lost original strict host preflight")
    generated, saved = map(read_archives, (before, after))
    reg = registry()

    def matched_parent(actual, local):
        return parent_delta(generated["parent"], actual, local, COUNTS[slot])

    observed = observe(after, "saved", prediction["edited"], request["self_appearance"]["appearance"],
                       request["display"], host["stages"]["original"]["child_labels"], reg, saved_parent=matched_parent)
    child = child_delta(generated["child"], saved["child"], reg)
    child["saved_definition_sha256"] = sha256(saved["child"].require("Contents/Definition")).hexdigest()
    child["exact_definition_replay"] = observed["child_definition"]["exact_replay"]
    renderer = observed["renderer"]
    labels = observed["child_labels"]
    label_frozen = label_differences(host["stages"]["generated"]["child_labels"], labels)
    baseline = host["stages"]["generated"]["strict_public_read"]
    require(observed["strict_public_read"] == baseline == host["stages"]["original"]["strict_public_read"]
            and baseline["passed"] and baseline["occurrences"] == COUNTS[slot]
            and baseline["diagnostic_codes"] == ["sldasm.native_record_unresolved"]
            and observed["linked_archive_streams"] == 13 and child["exact_definition_replay"]
            and observed["density_owner_matches"] and not observed["label_discrepancies"]
            and not label_frozen and set(labels) == {"width", "height"}
            and renderer["mapped_payload_equal"] and not renderer["native_renderer_field_differences"]
            and renderer["generated_allocator_retained"] is observed["passed"] is False,
            "native-saved density, renderer, labels or preserved original allocator predicate differs")
    com = excluded_modules()
    require(not com, "fresh saved SDK process imported a CAD runtime dependency")
    for pair in (before, after):
        for item in pair.values():
            exact(Path(item["file"]), item["sha256"])
    parent = dict(observed["parent_visual_replay"])
    parent.pop("parent_header_model")
    return {"pid": os.getpid(), "cad_runtime_imports": com,
            "frozen_sha256": {key: row["sha256"] for key, row in before.items()}, "saved_sha256": observed["sha256"],
            "strict_public_read": observed["strict_public_read"], "strict_public_write_refusal": observed["strict_source_write_refusal"],
            "strict_ordinary_definition_refusal": observed["strict_ordinary_definition"], "edited_depth_m": prediction["depth_edit_m"],
            "strict_public_read_matches_frozen_and_original_summary": True,
            "native_child_update_stamps": child_stamps,
            "strict_linked_archive_streams": observed["strict_archive_audits"], "parent": parent, "child": child,
            "same_mapped_renderer_values": True, "sketch_label_owners": {key: value["driver"] for key, value in labels.items()},
            "label_differences": {"from_native_original": observed["label_discrepancies"], "from_frozen_generated": label_frozen},
            "original_strict_outcome_passed": observed["passed"]}


def run(root, output):
    require(not output.resolve().is_relative_to(root), "supplement output must be outside the immutable packet")
    tree = check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT, text=True).strip()
    clean = run_process(("git", "diff", "--quiet", "HEAD", "--", "src"), cwd=ROOT, check=False)
    require(tree == SOURCE_TREE and clean.returncode == 0, "use the exact verified SDK tree for this supplement")
    packet, _ = inputs(root)
    results = {slot: subtask((Path(__file__).resolve(), "--packet", root, "--worker", slot)) for slot in TRIALS}
    processes = {row.pop("pid") for row in results.values()}
    require(len(processes) == len(TRIALS) and os.getpid() not in processes,
            "each disclosed saved pair requires its own fresh SDK process")
    exact(root / "Inspection" / "Result.json", RESULT_SHA256)
    report = {"schema": "kit.sw2026.disclosed-planar-renderer-native-save-delta.v1",
              "observed_revision": SOURCE_REVISION, "observed_sdk_tree": SOURCE_TREE,
              "original_result_sha256": RESULT_SHA256, "packet_sha256": PACKET_SHA256,
              "original_writer_revision": packet["writer_revision"], "original_writer_src_tree": packet["writer_src_tree"],
              "source_code_sha256": {name: file_sha(Path(__file__).with_name(name)) for name in OWN_FILES},
              "oracle_build": ORACLE_BUILD, "oracle_sha256": ORACLE, "original_native_processes": 8,
              "original_native_checks": 834, "original_native_mechanics_passed": True, "original_aggregate_passed": False,
              "new_post_save_read_processes": len(processes), "new_native_runs": 0, "new_heldout_credit": 0,
              "post_save_comparison_complete": True, "full_strict_saved_readback_passed": False, "cases": results}
    print(json.dumps({"report_sha256": write(output, report), "paired_saved_reads": len(results),
                      "full_strict_saved_readback_passed": False}))


def main():
    parser = ArgumentParser(description="Check the exact already observed planar renderer save transition")
    parser.add_argument("--packet", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--worker", choices=TRIALS)
    args = parser.parse_args()
    require(not args.packet.is_symlink(), "disclosed planar packet root must retain its actual location")
    root = args.packet.resolve(strict=True)
    if args.worker:
        print(json.dumps(worker(root, args.worker), sort_keys=True, allow_nan=False))
    else:
        run(root, args.output)


if __name__ == "__main__":
    main()
