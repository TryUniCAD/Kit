from itertools import product
from math import isfinite, pi


def world(frame, local):
    return tuple(
        frame["origin"][i]
        + sum(local[j] * frame[key][i] for j, key in enumerate(("u", "v", "normal")))
        for i in range(3)
    )


def predict(shape, edited_depth=None):
    depth = shape["depth"] if edited_depth is None else edited_depth
    if (
        not isinstance(depth, (float, int))
        or isinstance(depth, bool)
        or not isfinite(depth)
        or depth <= 0
    ):
        raise ValueError(
            "prediction requires an independently supplied positive total stock depth"
        )
    lower, upper = shape["stock"]["minimum"], shape["stock"]["maximum"]
    width, height = (upper[index] - lower[index] for index in range(2))
    center, radius = shape["tool"]["center"], shape["tool"]["radius"]
    both = shape["second_through_all"]
    sign = 1 if shape["cut_reversed"] else -1
    interval = (
        (-depth / 2, depth / 2) if both else tuple(sorted((0.0, sign * depth / 2)))
    )
    span = interval[1] - interval[0]
    stock_volume, removed = width * height * depth, pi * radius * radius * span
    volume = stock_volume - removed
    stock_center = tuple((lower[index] + upper[index]) / 2 for index in range(2)) + (
        0.0,
    )
    removed_center = (*center, (interval[0] + interval[1]) / 2)
    local_com = tuple(
        (stock_volume * stock_center[i] - removed * removed_center[i]) / volume
        for i in range(3)
    )
    corners = [
        world(shape["support"], point)
        for point in product(
            (lower[0], upper[0]), (lower[1], upper[1]), (-depth / 2, depth / 2)
        )
    ]
    return {
        "body_count": 1,
        "volume_m3": volume,
        "surface_area_m2": 2 * (width * height + width * depth + height * depth)
        + 2 * pi * radius * span
        - (2 * pi * radius * radius if both else 0.0),
        "center_of_mass_m": world(shape["support"], local_com),
        "bounds_m": {
            "minimum": tuple(min(point[i] for point in corners) for i in range(3)),
            "maximum": tuple(max(point[i] for point in corners) for i in range(3)),
        },
        "cut_interval_local_m": interval,
        "rim_centers_world_m": tuple(
            world(shape["support"], (*center, end)) for end in interval
        ),
        "face_count": 7 if both else 8,
        "edge_count": 14,
        "vertex_count": 10,
        "stock_driver_m": depth,
        "active_cut_dimensions": 0,
        "basis": "independent analytic rectangle-minus-cylinder integration from complete portable owners",
    }
