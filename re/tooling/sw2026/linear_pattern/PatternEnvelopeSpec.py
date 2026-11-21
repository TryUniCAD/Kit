from itertools import product
from math import dist, fsum, pi, sqrt
import json


PLATE = ((0.0, 0.0, 0.0), (0.120, 0.090, 0.00575))
SEED = ((0.087, 0.034, 0.0), (0.098, 0.043, 0.01225))
COMPONENT = 1 / sqrt(2)
NORMAL = (COMPONENT, COMPONENT, 0.0)
SPACING_VALUES = (0.020, 0.036)
PLANE_NAME = "EnvelopeDirection"
AXIS_NAME = "EnvelopeHinge"


def moved(box, distance):
    return tuple(tuple(value + distance * axis for value, axis in zip(point, NORMAL, strict=True)) for point in box)


def project(point):
    along = fsum(value * axis for value, axis in zip(point, NORMAL, strict=True))
    return tuple(value - along * axis for value, axis in zip(point, NORMAL, strict=True))


def measure(boxes):
    axes = tuple(sorted({point[axis] for box in boxes for point in box}) for axis in range(3))
    cells = {}
    for index in product(*(range(len(values) - 1) for values in axes)):
        lower = tuple(values[position] for values, position in zip(axes, index, strict=True))
        upper = tuple(values[position + 1] for values, position in zip(axes, index, strict=True))
        center = tuple((lo + hi) / 2 for lo, hi in zip(lower, upper, strict=True))
        if any(all(lo < value < hi for lo, value, hi in zip(first, center, last, strict=True)) for first, last in boxes):
            cells[index] = (center, tuple(hi - lo for lo, hi in zip(lower, upper, strict=True)))
    volumes, areas = [], []
    moments = [[], [], []]
    for index, (center, sides) in cells.items():
        volume = sides[0] * sides[1] * sides[2]
        volumes.append(volume)
        for axis in range(3):
            moments[axis].append(volume * center[axis])
            for direction in (-1, 1):
                neighbor = list(index)
                neighbor[axis] += direction
                if tuple(neighbor) not in cells:
                    areas.append(sides[(axis + 1) % 3] * sides[(axis + 2) % 3])
    total = fsum(volumes)
    lower = tuple(values[0] for values in axes)
    upper = tuple(values[-1] for values in axes)
    middle = tuple((lo + hi) / 2 for lo, hi in zip(lower, upper, strict=True))
    return {"bounds_m": (*lower, *upper), "volume_m3": total, "area_m2": fsum(areas),
            "centroid_m": tuple(fsum(values) / total for values in moments),
            "aabb_midpoint_m": middle, "projected_midpoint_m": project(middle)}


def specification():
    before = measure((PLATE, SEED))
    arms = []
    for spacing in SPACING_VALUES:
        replica = moved(SEED, spacing)
        inside_x = min(PLATE[1][0], replica[1][0]) - max(PLATE[0][0], replica[0][0])
        if not inside_x > 0 or not replica[0][0] > SEED[1][0] or not PLATE[0][1] < replica[0][1] < replica[1][1] < PLATE[1][1]:
            raise ValueError("replica must join only to the plate and remain wholly within its Y span")
        after = measure((PLATE, SEED, replica))
        arms.append({"spacing_m": spacing, "count": 2, "replica_bounds_m": replica,
                     "positive_overlap_x_m": inside_x, "expected_final": after,
                     "post_vs_pre_projected_distance_m": dist(after["projected_midpoint_m"], before["projected_midpoint_m"])})
    if not arms[0]["post_vs_pre_projected_distance_m"] == 0 or not arms[1]["post_vs_pre_projected_distance_m"] > 0.001:
        raise ValueError("envelope hypotheses are not separated")
    return {
        "schema": "kit.sw2026.linear-pattern-envelope-disclosed-spec.v1",
        "scope": "disclosed source authoring and geometry prediction only",
        "build": "34.5.2.0604",
        "plate_box_m": PLATE, "seed_box_m": SEED,
        "hinge": {"name": AXIS_NAME, "selection": [{"name": "Right Plane", "mark": 0}, {"name": "Top Plane", "mark": 0}],
                  "call": "IModelDoc2.InsertAxis2", "arguments": [True], "axis_model": [0, 0, 1]},
        "direction_datum": {"name": PLANE_NAME, "selection": [{"name": "Right Plane", "mark": 0}, {"name": AXIS_NAME, "mark": 1}],
                            "call": "IFeatureManager.InsertRefPlane", "arguments": [16, pi / 4, 4, 0.0, 0, 0.0],
                            "documented_flip_mask_if_needed": 256, "origin_m": [0.0, 0.0, 0.0],
                            "required_signed_normal": NORMAL},
        "pattern": {"definition_type": 6, "selection_marks": {"direction": 1, "seed": 4},
                    "direction_plane": PLANE_NAME, "single_direction": True, "feature_seed_name": "SeedBoss",
                    "bind_reversal_to_measured_signed_normal": True},
        "expected_before_pattern": before, "arms": arms,
        "ownership_hypotheses": {
            "pre_pattern_AABB": before["projected_midpoint_m"],
            "post_pattern_AABB_for_edited_spacing": arms[1]["expected_final"]["projected_midpoint_m"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(specification(), indent=2, sort_keys=True, allow_nan=False))
