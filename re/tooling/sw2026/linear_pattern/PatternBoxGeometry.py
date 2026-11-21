from math import dist, fsum, isfinite, prod

from CheckPatternAngleOwners import require
from PatternAngleGeometry import offsets
from PatternHingeGeometry import ORIGIN, box_points, joined_front_bounds


def contained_boxes(plate, seed, direction, spacing, count):
    joined_front_bounds(plate, seed)
    lower, upper = box_points(plate)
    first, last = box_points(seed)
    require(type(count) is int and 2 <= count <= 8 and type(spacing) in (int, float) and isfinite(spacing) and spacing > 0.0,
            "ordinary local pattern requires an active positive pitch and two to eight instances")
    require(len(direction) == 3 and all(type(value) is float and isfinite(value) for value in direction)
            and direction[2] == 0.0 and abs(dist(direction, ORIGIN) - 1.0) < 1e-14,
            "local pattern must use the actual signed direction in the seed sketch plane")
    parts = tuple((offsets(first, direction, spacing * index), offsets(last, direction, spacing * index)) for index in range(count))
    require(all(lower[0] < first[0] < last[0] < upper[0] and lower[1] < first[1] < last[1] < upper[1]
                for first, last in parts),
            "patterned raised footprints must all be wholly interior to the plate")
    require(all(any(max(alo[axis], blo[axis]) > min(ahi[axis], bhi[axis]) for axis in (0, 1))
                for index, (alo, ahi) in enumerate(parts) for blo, bhi in parts[:index]),
            "patterned raised footprints must remain strictly separated")
    return parts


def whole_solid_measure(plate, seed, direction, spacing, count):
    parts = contained_boxes(plate, seed, direction, spacing, count)
    lower, upper = box_points(plate)
    seed_low, seed_high = box_points(seed)
    width, height, thickness = upper
    sx, sy, sh = seed_high[0] - seed_low[0], seed_high[1] - seed_low[1], seed_high[2] - thickness
    plate_volume = prod(upper)
    raised_volume = sx * sy * sh
    volume = plate_volume + count * raised_volume
    origins = ((*first[:2], thickness) for first, _ in parts)
    raised_centres = tuple(tuple((a + b) * 0.5 for a, b in zip(first, last, strict=True))
                           for first, (_, last) in zip(origins, parts, strict=True))
    centroid = tuple(fsum([axis_span * 0.5 * plate_volume, *(point[axis] * raised_volume for point in raised_centres)]) / volume
                     for axis, axis_span in enumerate(upper))
    return {
        "body_count": 1, "face_count": 6 + 5 * count, "volume_m3": volume,
        "area_m2": 2 * (width * height + thickness * (width + height) + count * sh * (sx + sy)),
        "centroid_m": centroid, "bounds_m": (*lower, width, height, seed_high[2]), "instance_boxes_m": parts,
    }
