from hashlib import sha256
import json
from math import isfinite
import sys

from Predict import predict


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def propose(data):
    shape, coverage, policy = (
        data[name] for name in ("shape", "coverage", "edit_policy")
    )
    ratio, offset = (policy[name] for name in ("ratio", "offset_m"))
    if (
        any(
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not isfinite(value)
            for value in (ratio, offset)
        )
        or ratio <= 0
    ):
        raise ValueError(
            "edit policy requires an independently authored finite positive ratio and finite offset"
        )
    if (
        not coverage.get("source_owner_ids_preserved")
        or coverage.get("source_native_bytes_in_normalized_document") != 0
    ):
        raise ValueError(
            "lifecycle proposal must bind the complete byte-free owner inventory"
        )
    edited = shape["depth"] * ratio + offset
    before, after = predict(shape), predict(shape, edited)
    if edited == shape["depth"]:
        raise ValueError("lifecycle needs a real driving edit")
    history = coverage["ordered_source_history"]
    stock = next(
        row for row in history if row["source_id"] == shape["stock_feature_id"]
    )
    return {
        "status": "proposal_only_compilation_refused",
        "source_sha256": coverage["source_identity"]["sha256"],
        "shape_sha256": sha256(canonical(shape)).hexdigest(),
        "coverage_sha256": sha256(canonical(coverage)).hexdigest(),
        "edit_policy": policy,
        "stock_edit": {
            "source_parameter_id": shape["driver_id"],
            "source_feature_id": shape["stock_feature_id"],
            "native_dimension_name": "D1@" + stock["name"],
            "before_m": shape["depth"],
            "after_m": edited,
        },
        "predicted_before": before,
        "predicted_after": after,
        "configuration_name": shape["configuration_name"],
        "scope": shape["scope"],
        "source_history_count": len(history),
        "ordered_history_must_be_preserved": True,
        "active_cut_dimension_count": 0,
        "required_gates": [
            "complete actual system owner and presentation projection before construction",
            "actual independently read source and generated neutral history and dimensions",
            "source and generated native trees compared node by node with no caption filter",
            "zero load rebuild errors and warnings in every qualified phase",
            "independent volume area centre of mass and signed opening checks",
            "real stock D1 edit with no active cut distance",
            "save into new owned derivative; immutable originals",
            "fresh source and generated derivative reopens",
            "healthy bracketing controls in fresh processes",
        ],
        "unmapped_owners": coverage["blocking_owners"],
        "writer_output_count": 0,
        "held_out_accessed": False,
        "native_acceptance": False,
        "full_original_equivalence": False,
    }


def main():
    print(json.dumps(propose(json.load(sys.stdin)), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
