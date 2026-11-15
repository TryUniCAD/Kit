from __future__ import annotations

from math import isfinite

from Core import Obj
from builders.Sketch import ConstructionError, ProfileGraph, counted_fields, empty_object_list


def _driving_value(*, display: Obj, angular: bool):
    expected = "moDisplayAngularDim_c" if angular else "moDisplayDistanceDim_c"
    if not isinstance(display, Obj) or display.cls != expected:
        raise ConstructionError(f"end specifications require an actual {expected} node")
    handles = display.get("f850")
    if not isinstance(handles, (tuple, list)) or len(handles) != 1:
        raise ConstructionError("display dimension f850 must contain one constructed model-dimension handle")
    handle = handles[0].get("o")
    if not isinstance(handle, Obj):
        raise ConstructionError("display dimension f850[0].o must reference a model-dimension handle")
    dimension = handle.get("f100")
    expected_dimension = "AngleDim_c" if angular else "ParallelPlaneDistanceDim_c"
    if not isinstance(dimension, Obj) or dimension.cls != expected_dimension:
        raise ConstructionError(f"blind end dimension handle f100 requires {expected_dimension}")
    parameter = dimension.get("f28")
    expected_parameter = "moAngleParameter_c" if angular else "moLengthParameter_c"
    if not isinstance(parameter, Obj) or parameter.cls != expected_parameter:
        raise ConstructionError(f"driving dimension f28 requires {expected_parameter}")
    value = parameter.get("f58")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ConstructionError("driving parameter f58 requires a finite numeric value")
    return float(value)


def blind_end_spec(*, forward_distance: Obj, reverse_distance: Obj, forward_draft: Obj, reverse_draft: Obj):
    values = (forward_distance, reverse_distance, forward_draft, reverse_draft)
    if len({id(value) for value in values}) != len(values):
        raise ConstructionError("fresh end-spec dimensions require four distinct display nodes")
    depth = _driving_value(display=forward_distance, angular=False)
    reverse = _driving_value(display=reverse_distance, angular=False)
    if depth <= 0 or reverse != depth:
        raise ConstructionError("fresh blind end specifications require matching positive constructor depths")
    if _driving_value(display=forward_draft, angular=True) != 0 or _driving_value(display=reverse_draft, angular=True) != 0:
        raise ConstructionError("blind construction currently requires zero draft angles")
    return Obj("moEndSpec_c", {
        "f138": None,
        "f08": 1,
        "f88": 0,
        "f8c": 0,
        "f90": None,
        "f0c": 0,
        "f10": 0,
        "f18": forward_distance,
        "f20": reverse_distance,
        "has_f28": 0,
        "has_f48": 0,
        "fa0": 0.0,
        "fb8": 0,
        "fbc": 0,
        "fc0": 0,
        "fc4": 0,
        "fb0": 0,
        "fb4": 0,
        "fc8": forward_draft,
        "fd0": reverse_draft,
        "fa8": 0,
        "fac": 0,
        "fd8": 0,
        "fdc": 0,
        "fe0": empty_object_list(),
        "f100": empty_object_list(),
        "f128": 1,
        "f12c": 0,
        "f130": 0,
        "f140": Obj("moFromEndSpec_c", {"t": 0}),
        "f148": 0,
        "f14c": 0,
        "f150": 0,
        "f154": 0,
        "f158": 0,
    })


def blind_extrusion(*, feature: Obj, profile: ProfileGraph, end_spec: Obj, depth: float):
    if not isinstance(feature, Obj) or feature.cls != "moExtrusion_c":
        raise ConstructionError("blind extrusion requires an allocated moExtrusion_c body-feature node")
    for name in ("f08", "f28", "f60", "f368", "f388", "f780"):
        if name not in feature.f:
            raise ConstructionError(f"body-feature factory has not constructed required base field {name}")
    if type(feature["f08"]) is not int or feature["f08"] < 0 or type(feature["f28"]) is not int:
        raise ConstructionError("body-feature identifiers and flags must come from the allocated model factory node")
    if not isinstance(profile, ProfileGraph) or profile.point_count < 3 or profile.line_count != profile.point_count:
        raise ConstructionError("blind extrusion requires a constructed closed polygon profile graph")
    if not isinstance(end_spec, Obj) or end_spec.cls != "moEndSpec_c" or end_spec.get("f08") != 1 or end_spec.get("f0c") != 0 or end_spec.get("f10") != 0:
        raise ConstructionError("blind extrusion requires a single-ended blind moEndSpec_c")
    if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not isfinite(depth) or depth <= 0:
        raise ConstructionError("blind depth must be finite and positive")
    if _driving_value(display=end_spec.get("f18"), angular=False) != depth:
        raise ConstructionError("authored blind depth differs from its driving parameter")
    parents = feature["f60"]
    if parents.get("tail") != 0 or "list" not in parents:
        raise ConstructionError("fresh extrusion parent list must use the native empty-tail encoding")
    dependencies = list(parents["list"]["items"])
    if not any(item.get("o") is profile.profile for item in dependencies):
        dependencies.append({"o": profile.profile})
    parent_list = counted_fields(collections={"n": "items"})
    parent_list["items"].extend(dependencies)
    feature["f60"] = {"list": parent_list, "tail": 0}
    feature["f28"] |= 0x140
    feature["f818"] = end_spec
    feature["f838"] = 0.0
    feature["f810"] = -1
    return feature
