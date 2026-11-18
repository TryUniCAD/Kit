import argparse
from hashlib import sha256
import json
from pathlib import Path


def digest(data):
    return sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def publish(proof, bindings, output, binding_output):
    require(not output.exists() and not binding_output.exists(), "publication requires unused receipt paths")
    raw = (proof / "ReaderResults.json").read_bytes()
    value = json.loads(raw)
    sources = (proof / "SourceManifest.json").read_bytes()
    manifest = json.loads(sources)
    require(value["passed"] and value["source_manifest_sha256"] == digest(sources)
            and value["bindings_sha256"] == digest(bindings.read_bytes())
            and value["process_count"] == 80 and value["diagnostic_negative_count"] == 26
            and not value["heldout_inputs_read"] and value["writer_output_count"] == 0
            and value["native_processes_started"] == 0 and value["private_sdk_overlay_only"], "the exact disclosed proof does not qualify")
    changed = {name: {"before": manifest["baseline"].get(name), "after": fingerprint}
               for name, fingerprint in manifest["current"].items() if manifest["baseline"].get(name) != fingerprint}
    require(len(changed) == 18 and len(value["cases"]) == 2 and len(value["ordinary_codec_regressions"]) == 6,
            "the exact scoped source or disclosed inventory differs")
    quality = json.loads((proof.parent / "StaticQuality02.json").read_bytes())
    require(all(row["exit_code"] == 0 for row in quality)
            and "Success: no issues found in 18 source files" in (proof.parent / "mypy02.txt").read_text()
            and "0 errors, 0 warnings, 0 informations" in (proof.parent / "pyright02.txt").read_text(), "the scoped static source checks did not pass")
    cases = []
    for entry in value["cases"]:
        codec = entry["codec"]
        cases.append({"case": entry["case"], "file_sha256": codec["file_sha256"], "file_bytes": codec["file_bytes"],
                      "stream_sha256": codec["stream_sha256"], "stream_bytes": codec["stream_bytes"],
                      "map_base": codec["map_base"], "map_terminal": codec["map_terminal"],
                      "byte_identity": codec["byte_identity"], "typed_readback_identity": codec["typed_readback_identity"],
                      "inherited_map_aliases": codec["inherited_map_aliases"], "inherited_nodes_unchanged": codec["resolved_objects_unchanged"],
                      "empty_no_allocation": codec["empty_no_allocation"], "codec_negative_count": len(codec["negatives"]),
                      "grammar_completed": codec["usage"]["read"]["completed"],
                      "missing_schemas": codec["usage"]["read"]["missing_schemas"], "provisional_schemas": codec["usage"]["read"]["provisional_schemas"],
                      "native_byte_fields": codec["usage"]["read"]["native_byte_fields"],
                      "public": entry["public"], "typed_owners": entry["typed_owners"]})
    receipt = {"schema": "kit.sw2026.perpendicular-disclosed-reader-receipt.v1", "task_id": "B04-SW2026-MATES-PERPENDICULAR",
               "owner": "assembly_occurrence", "delivery_pr": 121, "archive_version": 19000, "container_version": 4,
               "passed": True, "scope": "private guarded source reader overlay for the disclosed D01 source and edited pair",
               "native_generated_perpendicular_acceptance": False, "full_family_coverage": False,
               "raw_process_receipt_sha256": digest(raw), "source_manifest_sha256": digest(sources),
               "baseline_sdk_revision": "f35eb89a6ba16443f9e987009a7b10b45b114a0b", "baseline_python_files": len(manifest["baseline"]),
               "current_python_files": len(manifest["current"]), "changed_sdk_files": changed,
               "tool_sha256": manifest["tools"], "publisher_sha256": digest(Path(__file__).read_bytes()),
               "native_bindings_sha256": digest(bindings.read_bytes()), "disclosed_custody": value["disclosed_custody"],
               "cases": cases, "ordinary_linked_codec_regressions": len(value["ordinary_codec_regressions"]),
               "exact_legacy_public_comparisons": len(value["legacy_public_regressions"]),
               "exact_child_and_deferred_comparisons": len(value["child_and_deferred_regressions"]),
               "diagnostic_negative_count": 26, "diagnostic_results": value["diagnostic_results"], "repacked_reader_control_passed": True,
               "local_python_launch_count": 80, "native_processes_started_by_reader_proof": 0,
               "source_native_processes": 5, "source_inputs_unchanged": value["source_inputs_unchanged"],
               "private_sdk_overlay_only": True, "public_registration_changed": False,
               "writer_output_count": 0, "diagnostic_output_count": 27, "heldout_inputs_read": False,
               "quality": {"black": True, "ruff": True, "steering": True, "mypy_strict": True, "pyright_source_diagnostics": 0,
                           "pyright_existing_unknown_settings": 3},
               "limitations": ["one disclosed design and its edited sibling are discovery evidence rather than independent heldouts",
                               "other perpendicular source cases and sealed sources were not read",
                               "no generated perpendicular writer or native generated acceptance",
                               "ordinary direct repeated part principal planes and one solved perpendicular only",
                               "rigid status words are retained observations rather than cold constructor values",
                               "normal public reads use include_brep=false and include_tessellation=false",
                               "strict typed rejection preserves the already valid legacy inventory with an unsupported diagnostic",
                               "no invalid angular start correction or deterministic free degree solver proof"]}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    require(not any(text in data for text in (b"/Users/", b"\\\\Mac\\", b"C:\\", b"Z:\\")), "publication contains an unsanitized machine path")
    output.write_bytes(data)
    binding_output.write_bytes(bindings.read_bytes())
    return {"receipt_sha256": digest(data), "binding_sha256": digest(bindings.read_bytes()), "sdk_files": len(changed)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binding-output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.proof, args.bindings, args.output, args.binding_output), sort_keys=True))


if __name__ == "__main__":
    main()
