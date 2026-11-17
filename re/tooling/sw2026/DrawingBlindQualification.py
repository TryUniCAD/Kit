from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ORDERED_MANIFEST = "ba27d8eb41a580553678995b9d863a1162325b2d3dcf17c31a9e5c8b96840293"
PREDECESSOR_MANIFEST = "c1e8e5788d32e9fbdfdae83b1ec95410835b2ee05c47a2a278dfc2ad88ae1de4"
CORRECTED_RECEIPT = "4d2021603b29662787eb19ecf4aa00a3b9c659e2e38ed13cbb8e68f02292a736"
ORDER_PROCESS_RECEIPT = "a5cf6630e981ed66a68327dbf44d8264c34dd56ab6e37d3cd504a719e9150870"
NEUTRAL_BINDING = "3611c049a520b0d3855d70c5e7da650dc5e24e18a41bb349f6cd849ad63b06e1"
PREDECESSOR_NATIVE = "674daf809255fdc3261aee698006fcc1af5f7b0644c25d9b4b2f4f1082622d07"
SOURCE_CHANGES = {
    "re/tooling/sw2026/builders/Model.py": (
        "74694cea3a8d74958f2a1c698bf71d456b838191d82fa53e378ee64c25ea6a93",
        "4bdd7397c1e7ba639fdb322a4b997c66ec0fc434341e830ac5adc274b0d4220e",
    ),
    "re/tooling/sw2026/builders/Part.py": (
        "b82c0dd08099e7c53f33dca6eb9a3f2dfbfaf6d8c156b41f80976f1afbcd1a3f",
        "199c4acaf0daf00bcb5477bd51e8717116c257d6aac0a00330a9829e82f63d6d",
    ),
}
QUALIFICATION_SCHEMA = "kit.sw2026.corrected-blind-drawing-qualification.v1"
FREEZE_SCHEMA = "kit.sw2026.original-blind-drawing-evaluation-freeze.v1"
GENERATION_SCHEMA = "kit.sw2026.original-blind-drawing-generation-freeze.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(path, expected):
    require(path is not None and expected is not None, "corrected drawing qualification requires every frozen evidence input")
    data = Path(path).read_bytes()
    require(sha256(data).hexdigest() == expected, "corrected drawing qualification evidence changed")
    return json.loads(data)


def verify_corrected(arguments, source, predecessor):
    require(arguments.writer_sources_sha256 == ORDERED_MANIFEST
            and arguments.profile_sources_sha256 == PREDECESSOR_MANIFEST
            and arguments.profile_result_sha256 == PREDECESSOR_NATIVE
            and arguments.neutral_binding_sha256 == NEUTRAL_BINDING,
            "held-out drawings require the exact corrected writer, independent intent and scaled predecessor")
    require(set(source["files"]) == set(predecessor["files"]) and len(source["files"]) == 3685,
            "corrected drawing writer source membership changed")
    changes = {name: (predecessor["files"][name], value) for name, value in source["files"].items()
               if predecessor["files"][name] != value}
    require(changes == SOURCE_CHANGES, "corrected drawing writer differs outside the proven authored-order hook")
    require(arguments.corrected_profile_sha256 == CORRECTED_RECEIPT
            and arguments.order_process_proof_sha256 == ORDER_PROCESS_RECEIPT,
            "held-out specification stays sealed until corrected native qualification and default reproduction are bound")
    receipt = checked(arguments.corrected_profile, arguments.corrected_profile_sha256)
    require(receipt["schema"] == "kit.sw2026.blind-standard-drawing-disclosed-native-receipt.v1"
            and receipt["mode"] == "disclosed" and receipt["passed"] and receipt["paired_semantic_profile_passed"]
            and receipt["controls_healthy"] and receipt["input_files_immutable"] and receipt["interpretable"]
            and receipt["distinct_processes"] == receipt["expected_processes"] == receipt["phase_count"] == 8
            and receipt["heldout_inputs_read"] == 0 and not receipt["complete_cad_acceptance"]
            and receipt["writer_source_manifest_sha256"] == ORDERED_MANIFEST
            and receipt["neutral_binding_sha256"] == NEUTRAL_BINDING
            and receipt["raw_result_sha256"] == "df1e8b086d1feeb81bfa4a74113a8d2655a3df2fb258282c90d57d6b3b3769b0"
            and receipt["host_report_sha256"] == "6a5738d529aaa97f2c2359d796fbfcc2c3be384c84180d5a88a1c5d7eee3d0c8"
            and receipt["packet_sha256"] == "9cf0198b96f2282693924a76e2da701a7d830fbdb8d3315533d8373a21c5d787"
            and receipt["case"]["name"] == "D01FrontView" and receipt["case"]["passed"]
            and receipt["case"]["compared_value_count"] == 950 and receipt["case"]["mismatch_count"] == 0
            and all(row["passed"] and not row["mismatches"] for row in receipt["case"]["reports"]),
            "corrected drawing native paired qualification did not pass")
    process = checked(arguments.order_process_proof, arguments.order_process_proof_sha256)
    require(process["passed"] and process["all_default_artifacts_identical"] and process["source_closure_immutable"]
            and process["writer_source_manifest_sha256"] == ORDERED_MANIFEST
            and process["prior_source_manifest_sha256"] == PREDECESSOR_MANIFEST
            and process["guarded_successful_builds"] == 12 and process["fresh_processes"] == 19
            and process["runtime_input_file_access_attempts"] == 0 and process["heldout_inputs_read"] == 0
            and not process["vendor_runtime_executed"] and not process["native_acceptance"]
            and all(row["complete_report_identical"] for row in process["default_cases"])
            and all(row["rejected"] and row["output_bytes"] == 0 for row in process["invalid_requests"]),
            "corrected drawing default-byte reproduction did not pass")
    return {"schema": QUALIFICATION_SCHEMA, "qualified": True,
            "writer_source_manifest_sha256": ORDERED_MANIFEST, "predecessor_source_manifest_sha256": PREDECESSOR_MANIFEST,
            "scaled_native_result_sha256": PREDECESSOR_NATIVE, "corrected_native_receipt_sha256": CORRECTED_RECEIPT,
            "order_process_proof_sha256": ORDER_PROCESS_RECEIPT, "neutral_binding_sha256": NEUTRAL_BINDING,
            "heldout_inputs_read": 0, "complete_cad_acceptance": False}
