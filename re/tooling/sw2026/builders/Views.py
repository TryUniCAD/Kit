from __future__ import annotations

import math

from Core import ArchiveError, Obj


def _multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        ((ax * bw + bx * aw) + ay * bz) - az * by,
        ((by * aw - bz * ax) + ay * bw) + az * bx,
        ((by * ax + bz * aw) - ay * bx) + az * bw,
        ((bw * aw - ax * bx) - by * ay) - az * bz,
    )


def _rotation(axis, angle):
    sine, cosine = math.sin(angle * -0.5), math.cos(angle * -0.5)
    return (*(component * sine for component in axis), cosine)


def _matrix(quaternion):
    x, y, z, w = quaternion
    x2, y2, z2 = x + x, y + y, z + z
    xx, xy, xz = x * x2, x * y2, x * z2
    yy, yz, zz = y * y2, y * z2, z * z2
    wx, wy, wz = w * x2, w * y2, w * z2
    rows = (
        (1 - (zz + yy), xy - wz, wy + xz),
        (wz + xy, 1 - (zz + xx), yz - wx),
        (xz - wy, wx + yz, 1 - (yy + xx)),
    )
    values = []
    for vx, vy, vz in rows:
        length_squared = (vx * vx + vy * vy) + vz * vz
        if length_squared < 1e-17:
            raise ArchiveError("a canonical view rotation produced a zero row")
        inverse_length = 1.0 / math.sqrt(length_squared)
        values.extend(component * inverse_length for component in (vx, vy, vz))
    return {f"m{index}": value for index, value in enumerate(values)}


def _transform(matrix=None):
    fields = {"has_matrix": int(matrix is not None), "f58": 0.0, "f60": 0.0, "f68": 0.0, "f70": 1.0, "f78": 0}
    if matrix is not None:
        fields["f08"] = matrix
    return fields


def standard_views(*, detail_standard):
    if type(detail_standard) is not int or detail_standard != 1:
        raise ArchiveError("fresh canonical views require the classified effective detail-standard field 1")
    identity = (0.0, 0.0, 0.0, 1.0)
    x_axis, y_axis = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    plans = (
        (), (),
        ((y_axis, 3.1415926535898002),),
        ((y_axis, 1.5707963267949001),),
        ((y_axis, -1.5707963267949001),),
        ((x_axis, 1.5707963267949001),),
        ((x_axis, -1.5707963267949001),),
        ((y_axis, -0.78539816339745006), (x_axis, 0.61540309425319417)),
        ((y_axis, -0.48555059790479999), (x_axis, 0.54105206811819995)),
        ((y_axis, -0.36136712382000002), (x_axis, 0.33983690937)),
    )
    names = ("*Normal To", "*Front", "*Back", "*Left", "*Right", "*Top", "*Bottom", "*Isometric", "*Trimetric", "*Dimetric")
    result = []
    for index, (name, plan) in enumerate(zip(names, plans, strict=True)):
        quaternion = identity
        for axis, angle in plan:
            quaternion = _multiply(quaternion, _rotation(axis, angle))
        result.append({"o": Obj("moView_c", {
            "f358": name, "f368": _transform(None if index < 2 else _matrix(quaternion)),
            "f370": _transform(), "f388": 0, "f38c": -1, "f378": -1.0,
            "n380": 0, "f380": [], "f360": index, "f394": 0, "n398": 0,
            "f3a8": 0, "f3b8": 0.0, "n3b0": 0, "f3c0": 0, "f3c8": 0,
        }, schema=1)})
    return result
