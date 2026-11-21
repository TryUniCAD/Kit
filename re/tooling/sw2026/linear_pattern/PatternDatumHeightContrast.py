from math import dist, sqrt
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PatternEnvelopeSpec import PLATE, SEED, measure, moved, specification


HEIGHTS = (0.008625, 0.020375)
PITCH_M = 0.020
POINT_TOLERANCE_M = 5e-9


def predict_height(height):
    seed = (SEED[0], (*SEED[1][:2], height))
    replica = moved(seed, PITCH_M)
    if not PLATE[1][2] < height or not seed[1][0] < replica[0][0] < replica[1][0] < PLATE[1][0]:
        raise ValueError("require distinct raised copies entirely joined to the plate")
    before = measure((PLATE, seed))
    after = measure((PLATE, seed, replica))
    if before["bounds_m"] != after["bounds_m"]:
        raise ValueError("changing the solid envelope during pattern creation would confound this contrast")
    half_hinge_span = height * (0.5 + 0.05)
    component = half_hinge_span / sqrt(2)
    display_midpoint = (component, component, height / 2)
    return {
        "seed_box_m": seed, "seed_depth_m": height, "spacing_m": PITCH_M, "instances": 2,
        "prior_solid": before, "final_solid": after,
        "expected_stock_projection_m": before["projected_midpoint_m"],
        "hypothesized_hinge_endpoints_m": ((0, 0, height * 1.05), (0, 0, -height * 0.05)),
        "hypothesized_display_projection_m": display_midpoint,
        "hypothesized_display_distance_from_stock_projection_m": dist(display_midpoint, before["projected_midpoint_m"]),
        "hypothesized_display_transverse_m": half_hinge_span,
    }


def prediction():
    existing = specification()
    arms = [predict_height(height) for height in HEIGHTS]
    if arms[0]["expected_stock_projection_m"][:2] != arms[1]["expected_stock_projection_m"][:2]:
        raise ValueError("stock transverse prediction changed")
    shift = dist(*(arm["hypothesized_display_projection_m"][:2] for arm in arms))
    if shift <= 0.005 or any(arm["hypothesized_display_distance_from_stock_projection_m"] < 0.05 for arm in arms):
        raise ValueError("insufficient separation of the proposed datum owners")
    return {
        "schema": "kit.sw2026.linear-pattern-datum-height-prospective.v1",
        "cohort": "disclosed proposal", "build": existing["build"], "plate_box_m": PLATE,
        "hinge": existing["hinge"], "direction_datum": existing["direction_datum"], "pattern": existing["pattern"],
        "arms": arms, "candidate_display_transverse_shift_m": shift,
        "comparison_tolerance_m": POINT_TOLERANCE_M,
        "stage": "sample both native display diagonals before creating the pattern and after fresh reopen",
        "compute": "compare average of the actual model-space diagonal endpoints to the stored line point",
        "limits": "height-based display numbers are a hypothesis; compare FC8 to measured datum geometry",
    }


if __name__ == "__main__":
    print(json.dumps(prediction(), indent=2, sort_keys=True, allow_nan=False))
