from math import isclose


def contour_roles(case):
    axis = case["axis_x_m"]
    left, right = (axis + radius for radius in case["radius_m"])
    bottom, top = case["axial_m"]
    corners = ((left, bottom), (right, bottom), (right, top), (left, top))
    return tuple(tuple(sorted((point, corners[(index + 1) % 4]))) for index, point in enumerate(corners))


def edge_role(roles, points):
    endpoints = sorted(tuple(point) for point in points)
    matches = [index for index, ends in enumerate(roles) if all(
        isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
        for point, target in zip(endpoints, ends, strict=True)
        for actual, expected in zip(point, target, strict=True)
    )]
    if len(matches) != 1:
        raise ValueError("native relation owner does not select an actual rectangle edge")
    return matches[0]
