from __future__ import annotations

from collections.abc import Sequence
from math import isfinite, sqrt
from ntpath import basename, splitext

from Core import Obj


def bounding_box(*, minimum: Sequence[float], maximum: Sequence[float]) -> dict:
    points = []
    for name, point in (("minimum", minimum), ("maximum", maximum)):
        if not isinstance(point, Sequence) or isinstance(point, (str, bytes, bytearray)) or len(point) != 3:
            raise ValueError(f"{name} must contain three coordinates in native model space")
        if any(type(value) not in (int, float) for value in point):
            raise ValueError(f"{name} coordinates must be real numbers")
        try:
            values = tuple(float(value) for value in point)
        except OverflowError as error:
            raise ValueError(f"{name} coordinates exceed the archive numeric domain") from error
        if not all(isfinite(value) for value in values):
            raise ValueError(f"{name} coordinates must be finite")
        points.append(values)
    low, high = points
    if any(a > b for a, b in zip(low, high, strict=True)):
        raise ValueError("minimum coordinates must not exceed maximum coordinates")
    center = tuple((a + b) * 0.5 for a, b in zip(low, high, strict=True))
    dx, dy, dz = (b - a for a, b in zip(low, high, strict=True))
    radius = sqrt(dx * dx + dy * dy + dz * dz) * 0.5
    values = (*center, *high, *low, radius)
    if not all(isfinite(value) for value in values):
        raise ValueError("derived bounding-box state exceeds the archive numeric domain")
    return {f"b{index}": value for index, value in enumerate(values)}


def file_definition(*, path_name: str, document_kind: str, created_at: int) -> dict:
    if not isinstance(path_name, str) or not path_name or "\x00" in path_name:
        raise ValueError("file references require an explicit nonempty path without null characters")
    if document_kind not in ("part", "assembly"):
        raise ValueError("fresh file definitions support native part and assembly documents")
    if type(created_at) is not int or not 0 <= created_at <= 0xFFFFFFFF:
        raise ValueError("referenced document creation time must fit the archive timestamp field")
    name, extension = splitext(basename(path_name))
    required_extension = ".sldprt" if document_kind == "part" else ".sldasm"
    if not name or extension.lower() != required_extension:
        raise ValueError("reference path extension must agree with its native document kind")
    return {
        "h18": Obj("moCStringHandle_c", {"f08": path_name}),
        "h10": Obj("moCStringHandle_c", {"f08": name}),
        "f20": 2 if document_kind == "part" else 3,
        "f08": 0,
        "f28": created_at,
        "f38": "",
        "f40": "",
        "f50": "",
        "f35": 0,
    }


def referenced_configuration(*, name: str | None, local_id: int | None) -> dict:
    if name is None and local_id is None:
        return {"f08": "", "f10": -1}
    if not isinstance(name, str) or not name or "\x00" in name:
        raise ValueError("referenced configuration names must be explicit nonempty strings")
    if type(local_id) is not int or not 0 <= local_id < 0x7FFFFFFF:
        raise ValueError("referenced configuration ids must identify an actual generated configuration")
    return {"f08": name, "f10": local_id}
