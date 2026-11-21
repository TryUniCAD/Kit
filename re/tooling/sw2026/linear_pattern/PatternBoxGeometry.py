from math import fsum, prod

from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatBoxes import (
    MakePatBoxes as contained_boxes,
)

from PatternHingeGeometry import box_points


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
