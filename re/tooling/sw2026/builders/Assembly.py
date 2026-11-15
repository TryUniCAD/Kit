from __future__ import annotations

from collections.abc import Sequence
from math import isfinite, sqrt
from ntpath import basename, splitext

from Core import Obj
from builders.Model import base_configuration_fields, object_list


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


def _initial_configuration_options() -> Obj:
    fields = {name: 0 for name in (
        "f14", "f28", "f20", "f34", "f40", "f58", "f5c", "f60",
        "f68", "f6c", "f70", "f74",
    )}
    fields.update({
        "f08": 2, "f0c": 1, "f10": 1, "f18": 2,
        "f38": 6, "f3c": 1, "f48": "", "f50": -1, "f64": -1,
    })
    return Obj("moConfig_c", fields)


def _initial_component_configuration() -> Obj:
    return Obj("moConfigObject_c", {
        "f08": _initial_configuration_options(),
        "f10": None,
        "f28": referenced_configuration(name=None, local_id=None),
        "f40": None,
        "f48": {"f08": object_list(), "f28": 101},
        "has_f140": 0,
        "f78": object_list(),
        "f18": 0x111,
        "f20": 0,
        "f148": 0,
        "has_f170": 0,
        "fc0": None,
        "fc8": None,
        "f178": "",
        "f190": 0,
        "f118": object_list(),
        "fd0": object_list(),
    })


def initial_configuration(
    *,
    name: str,
    owner: Obj,
    local_id: int,
    date_code: int,
    parasolid_version: int,
    updated_at: int,
    description: str = "",
) -> Obj:
    result = Obj("moConfiguration_c")
    fields = base_configuration_fields(
        node=result, name=name, owner=owner, local_id=local_id,
        date_code=date_code, parasolid_version=parasolid_version,
        updated_at=updated_at, description=description,
    )
    fields["f0c"] &= 0xFFFD7FF8
    fields.update({
        "fc48": _initial_configuration_options(),
        "fc50": _initial_configuration_options(),
        "fca0": None,
        "fca8": None,
        "fce8": [{"o": _initial_component_configuration()}],
        "fba8": None,
        "fbb0": None,
        "fbc0": 0,
        "fbc4": 1,
        "fbc8": None,
        "fce0": None,
    })
    return result
