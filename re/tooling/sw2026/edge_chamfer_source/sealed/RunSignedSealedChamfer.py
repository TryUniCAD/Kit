from pathlib import PureWindowsPath

from RunSealedChamfer import (
    BOUNDARY_REV, BUILD, DRIVER_REV, EPOCH, LOCK_REV, ORACLE, PRIOR_FREEZE, PRIOR_RESULT, PUBLIC_ASSETS,
    SIGNED_EVAL_ROOT, SLOTS, SOURCE_PATH, WRITER, custody_result, main, pin_record, read_freeze, require,
    valid_hash, verify_original_public_evidence, verify_public_members,
)

TRIAL = "GeneratedChamferHeldout03"
PUBLIC = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / TRIAL
SCHEMA = "kit.sw2026.generated-chamfer-heldout-freeze.v3"
SIGNED_WRITER = "240492e95dcf7743c2847615fe28b83bd5adc78e"
SIGNED_TREE = "382e33fbf51377560364296a62e97f7d611e5eb5"
SIGNED_SRC_TREE = "392993e1c5f530d854c132482b268d1554d8c5c7"
SIGNED_COMPILER_SHA = "1023ea18efb9ea614ec74db84e79feb0b07a100021e66ecc68596b44e5619dda"
SIGNED_DISCLOSED_TRIAL = "8db08a479cd2b3e29dd4d5ad38eec3e96631e0aec15f71868a37aea51d423f49"
SIGNED_NATIVE_RESULT = "d161909999b3ed8d72f0885dbb6dbc0dfa3866e712dc4dd390aef7406c236409"
SIGNED_DISCLOSED_SOURCE = "2bce5961120ea7d8ea95ceaa5c10f7cbdbe6338152833357304647f432b86ff8"
SIGNED_SOURCE_AUDIT = "f1f841e2c6851522ce7c10bf5c469c92ded68db0fd50e1f3caed98a334aa89d7"
SIGNED_INPUTS = (
    "a7920a064cfb41876d42393bb3711c3cfe84d2fc742016812d09bb0ff459765a",
    "77d7292d2ccb45807479612f8f55e6f934e65a855d34213ffe4ed199193281ad",
)
PRIOR_FREEZE02 = "d95ad3efc026334254f76e05c0d66671ed137d9959f980299c1d19904d264057"
PRIOR_RESULT02 = "00f72e7f3265e00bc61aa979508adfe5da6415a4c866525a21710aa48dc3daef"
PRIOR_CUSTODY02 = "aa3b5565addc572b0ead42658e29766429b8d6c65b0396715e7ffebbf42f96bd"
ASSETS = PUBLIC_ASSETS | {
    "Tool/RunSignedSealedChamfer.py", "SignedTrial.json", "SignedNativeResult.json",
    "PriorEvaluation02.json", "PriorCustody02.json",
}


def verify_signed_plan(plan):
    require(plan["schema"] == "kit.sw2026.chamfer-cold-candidate-trial.v1"
            and plan["oracle_build"] == BUILD and plan["oracle_sha256"] == ORACLE
            and plan["construction_revision"] == SIGNED_WRITER and plan["construction_src_tree"] == SIGNED_SRC_TREE
            and plan["disclosed_source_lock_sha256"] == SIGNED_DISCLOSED_SOURCE
            and plan["source_audit_sha256"] == SIGNED_SOURCE_AUDIT
            and plan["guarded_generation_processes"] == 4
            and plan["guarded_runtime_reads"] == plan["heldout_inputs_read"] == plan["heldout_credit"] == 0
            and tuple(row["archive_sha256"] for row in plan["cases"]) == SIGNED_INPUTS
            and [row["reciprocal"] for row in plan["cases"]] == [True, False],
            "signed disclosed trial must be the exact independently frozen modeled pair")
    for row in plan["cases"]:
        proof = row["writer_proof"]
        require(proof["runtime_accesses"] == 0 and proof["driver_count"] == proof["linked_streams_exact"] == 2
                and proof["streams"] == len(proof["stream_sha256"]) == 10
                and proof["archive_sha256"] == row["archive_sha256"], "signed disclosed writer proof differs")


def verify_signed_result(receipt):
    require(receipt["schema"] == "kit.sw2026.chamfer-cold-candidate-trial.v1"
            and receipt["manifest_sha256"] == SIGNED_DISCLOSED_TRIAL
            and receipt["passed"] is True and receipt["healthy_controls"] is True
            and receipt["proper_distinct_lifetimes"] is True and receipt["lifecycle_slots"] == [0, 1]
            and receipt["orchestration_failure"] is None and receipt["heldout_credit"] == 0,
            "both independently disclosed signed lifecycles must pass on the exact frozen writer")
    phases = receipt["phases"]
    expected = [("before", None), ("edit", 0), ("reopen", 0), ("edit", 1), ("reopen", 1), ("after", None)]
    require([(row["role"], row["slot"]) for row in phases] == expected
            and all(row["phase_passed"] is True and row["timed_out"] is False and row["exit_code"] == 0
                    and valid_hash(row["receipt_sha256"]) and len(row["lifetime"]) == 2
                    and all(type(value) is int and value > 0 for value in row["lifetime"]) for row in phases)
            and len({tuple(row["lifetime"]) for row in phases}) == 6,
            "signed native phase receipts did not attest six distinct healthy processes")
    comparisons = receipt["disclosed_source_comparisons"]
    require([row["slot"] for row in comparisons] == [0, 1]
            and all(row["passed"] is True and [phase["phase"] for phase in row["phases"]] == ["open", "edited", "reopen"]
                    and all(phase["passed"] is True and phase["numeric_checks"] == 23 for phase in row["phases"])
                    for row in comparisons),
            "signed native pair did not pass every exact source state comparison")


def verify_previous_retry(packet, prewriter):
    custody = pin_record(packet / "PriorCustody02.json", PRIOR_CUSTODY02)
    require(custody == custody_result(PRIOR_FREEZE02, prewriter, 2, 6, 8, 0),
            "the earlier native preflight does not attest this same locked cohort")
    prior = pin_record(packet / "PriorEvaluation02.json", PRIOR_RESULT02)
    require(prior["freeze_sha256"] == PRIOR_FREEZE02 and prior["custody_receipt_sha256"] == PRIOR_CUSTODY02
            and prior["source_lock_sha256"] == prewriter["source_lock_sha256"]
            and prior["construction_revision"] == WRITER and prior["oracle_build"] == BUILD and prior["oracle_sha256"] == ORACLE
            and prior["passed"] is False and prior["heldout_lifecycle_credit"] == 0 and prior["distinct_fresh_processes"] == 8
            and prior["healthy_controls"] is True and prior["oracle_idle_after"] is True
            and prior["source_immutability_verified"] is True and [row["slot"] for row in prior["slots"]] == list(SLOTS),
            "the preserved second result does not belong to the same immutable matched retry")
    first, second = prior["slots"]
    require(first["passed"] is True and first["stage"] == "complete" and first["paired_states"] == 3
            and first["paired_numeric_checks"] == 115 and first["runtime_accesses"] == 0
            and second["passed"] is False and second["stage"] == "generation" and second["paired_states"] == 0
            and "archive_sha256" not in second and valid_hash(second["failure_sha256"]),
            "the earlier scoped refusal and independent completed slot have changed")


def verified(packet, pin):
    freeze = read_freeze(packet, pin)
    expected = {
        "schema": SCHEMA, "construction_revision": SIGNED_WRITER, "construction_tree": SIGNED_TREE,
        "construction_src_tree": SIGNED_SRC_TREE, "prewriter_lock_revision": LOCK_REV,
        "boundary_revision": BOUNDARY_REV, "driver_revision": DRIVER_REV, "oracle_build": BUILD, "oracle_sha256": ORACLE,
        "source_root": SOURCE_PATH, "evaluation_root": str(SIGNED_EVAL_ROOT),
        "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT,
        "prior_freeze02_sha256": PRIOR_FREEZE02, "prior_result02_sha256": PRIOR_RESULT02,
        "prior_custody02_sha256": PRIOR_CUSTODY02, "signed_trial_sha256": SIGNED_DISCLOSED_TRIAL,
        "signed_native_result_sha256": SIGNED_NATIVE_RESULT,
        "complete_fresh_processes": 10, "epochs": [EPOCH, EPOCH + 1],
    }
    require(all(freeze[key] == value for key, value in expected.items()) and valid_hash(freeze["evaluator_revision"], 40),
            "signed evaluation code, immutable source custody or native evidence is unbound")
    verify_public_members(packet, freeze["files"], ASSETS, SIGNED_COMPILER_SHA)
    prewriter = verify_original_public_evidence(packet)
    verify_previous_retry(packet, prewriter)
    verify_signed_plan(pin_record(packet / "SignedTrial.json", SIGNED_DISCLOSED_TRIAL))
    verify_signed_result(pin_record(packet / "SignedNativeResult.json", SIGNED_NATIVE_RESULT))
    return freeze, prewriter


if __name__ == "__main__":
    main(verified, PUBLIC, SIGNED_EVAL_ROOT)
