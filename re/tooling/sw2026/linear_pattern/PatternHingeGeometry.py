from math import isfinite


ORIGIN = (0.0, 0.0, 0.0)
AXIS = (0.0, 0.0, -1.0)
MINIMUM_SPAN_M = 1e-7
EDGE_FRACTION = 0.05


def box_points(box):
    low, high = (tuple(point) for point in box)
    if (len(low) != 3 or len(high) != 3 or not all(type(value) in (int, float) and isfinite(value) for value in (*low, *high))
            or not all(upper - lower > MINIMUM_SPAN_M for lower, upper in zip(low, high, strict=True))):
        raise ValueError("expected a finite positive size box in model coordinates")
    return low, high


def joined_front_bounds(plate, seed):
    plate_low, plate_high = box_points(plate)
    seed_low, seed_high = box_points(seed)
    if (plate_low != ORIGIN or seed_low[2] != 0.0 or not plate_high[2] < seed_high[2]
            or not all(plate_low[axis] < seed_low[axis] < seed_high[axis] < plate_high[axis] for axis in (0, 1))):
        raise ValueError("expected an origin plate and an interior raised Front-plane seed with a common start")
    return ORIGIN, (plate_high[0], plate_high[1], seed_high[2])


def principal_displays(box):
    low, high = box_points(box)
    if low != ORIGIN:
        raise ValueError("this local construction requires the canonical origin plate")
    center = tuple((upper + lower) * 0.5 for lower, upper in zip(low, high, strict=True))
    spans = tuple(upper - lower for lower, upper in zip(low, high, strict=True))
    half_x, half_y, half_z = (span * 0.5 + span * EDGE_FRACTION for span in spans)
    x, y, z = center
    return {
        "Top Plane": {"display_root_m": (x, 0.0, z), "borders_m": (half_x, -half_x, half_z, -half_z)},
        "Right Plane": {"display_root_m": (0.0, y, z), "borders_m": (half_z, -half_z, half_y, -half_y)},
    }


def derive_hinge(plate, seed):
    before_pattern = joined_front_bounds(plate, seed)
    displays = principal_displays(before_pattern)
    top = displays["Top Plane"]
    center_x, _, center_z = top["display_root_m"]
    u_high, u_low, v_high, v_low = top["borders_m"]
    start_z, finish_z = center_z - v_low, center_z - v_high
    if not center_x + u_low < 0.0 < center_x + u_high or not start_z > 0.0 > finish_z:
        raise ValueError("selected hinge must cross the interior of the finite Top display rectangle")
    return {
        "before_pattern_box_m": before_pattern,
        "principal_displays": displays,
        "root_m": ORIGIN,
        "direction": AXIS,
        "ordered_endpoints_m": ((0.0, 0.0, start_z), (0.0, 0.0, finish_z)),
        "ordered_distances_m": (start_z, -finish_z),
    }
