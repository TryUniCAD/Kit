from math import isfinite, sqrt


def dot(left, right):
    x, y, z = (a * b for a, b in zip(left, right, strict=True))
    return (x + y) + z


def unit(vector):
    squared_length = dot(vector, vector)
    if not isfinite(squared_length) or squared_length < 1e-17:
        raise ValueError("direction resolver requires a finite nondegenerate vector")
    reciprocal_length = 1.0 / sqrt(squared_length)
    return tuple(reciprocal_length * value for value in vector)


def cross(left, right):
    a, b, c = left
    x, y, z = right
    return b * z - c * y, c * x - a * z, a * y - b * x


def resolve_local_plane(display_origin, horizontal, normal, borders):
    if len(display_origin) != 3 or not all(isfinite(value) for value in display_origin):
        raise ValueError("a finite datum display origin is required")
    if (abs(dot(horizontal, horizontal) - 1.0) > 1e-14 or abs(dot(normal, normal) - 1.0) > 1e-14
            or abs(dot(horizontal, normal)) > 1e-14):
        raise ValueError("the ordinary local datum must have an orthonormal display frame")
    b0, b1, b2, b3 = borders
    if not all(isfinite(value) for value in borders) or not (b0 > b1 and b2 > b3):
        raise ValueError("the datum display rectangle must be finite with two positive spans")
    vertical = unit(cross(normal, horizontal))
    perimeter = ((b1, b2), (b0, b2), (b0, b3), (b1, b3))
    corners = tuple(tuple(p + (s * a + t * b)
                          for p, a, b in zip(display_origin, horizontal, vertical, strict=True))
                    for s, t in perimeter)
    center = tuple(((((0.0 + a) + b) + c) + d) * 0.25 for a, b, c, d in zip(*corners, strict=True))
    second = tuple(point + axis for point, axis in zip(center, normal, strict=True))
    displacement = tuple(b - a for a, b in zip(center, second, strict=True))
    direction = unit(displacement)
    return {"fc8": center, "fe0": direction, "fb0": 0.0, "fb8": dot(displacement, direction), "f68": 1}
