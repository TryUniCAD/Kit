from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from struct import pack, unpack

from Core import Obj
from builders.Sketch import ConstructionError, DerivedFields, PlaneFrame, ProfileGraph, counted_fields, dimension_fields, empty_object_list, frame_transform


def _point(*, x=0.0, y=0.0, z=0.0):
    return {"x": x, "y": y, "z": z}


def _identity_transform():
    return frame_transform(frame=PlaneFrame(origin=(0.0, 0.0, 0.0), u=(1.0, 0.0, 0.0), v=(0.0, 1.0, 0.0)))


def _raw_identity_transform():
    matrix = tuple(float(row == column) for row in range(3) for column in range(3))
    raw = pack("<9dII4dII", *matrix, 1, 0, 0.0, 0.0, 0.0, 1.0, 0, 0)
    return {"words": tuple({"w": word} for word in unpack("<30I", raw))}


def _dimension_text(*, angular: bool):
    fields = counted_fields(collections={"n90": "f98"}, fields={
        "f08": "",
        "f38": _point(),
        "f10": 13 if angular else 2,
        "f18": None,
        "f20": 0,
        "f50": _point(),
        "f68": 1.0,
        "fc4": 0,
        "fa0": 0,
        "fd0": 0,
        "fd8": 1e-6,
        "fe0": 1e-6,
        "f24": 0,
        "f0f0": counted_fields(collections={"n": "items"}),
        "f118": 0,
        "f120": 0,
        "f124": 0,
        "f128": 1.0,
        "f130": 0,
    })
    return fields


def common_display_fields(*, handle: Obj, angular: bool, design_intent: bool, selected_leader: int):
    if type(design_intent) is not bool:
        raise ConstructionError("display design intent must be an authored boolean")
    if type(selected_leader) is not int or not -(1 << 31) <= selected_leader < (1 << 31):
        raise ConstructionError("display selected leader must be an explicit signed 32-bit presentation value")
    fields = counted_fields(collections={
        "n2b0": "f2b0", "n3d0": "f3c0", "n2e8": "f2e0", "n4a8": "f4a8",
        "n4f0": "f4f0", "n550": "f550", "n850": "f850",
    }, fields={
        "f50": 0,
        "f30": None,
        "f40": None,
        "f48": None,
        "f54": 0,
        "f11c": 0,
        "f08": {"f00": 0xFFFF, "f02": 0, "f04": 3, "f08": {"f00": 0xFFFFFFFF, "f04": 0, "f08": {"f06": 0, "f00": -1.0}}},
        "f68": empty_object_list(),
        "fb0": empty_object_list(),
        "f58": 0,
        "ff8": None,
        "linked": 0,
        "f118": 19000,
        "f390": 0,
        "f3e0": 0x80080,
        "f290": _point(),
        "has_f298": 0,
        "has_f288": 0,
        "f3f8": None,
        "f400": _point(),
        "f2a0": _identity_transform(),
        "has_f2c0": 0,
        "f2c8": 0.0,
        "has_f2d0": 0,
        "f2d8": None,
        "f3b8": -1.0,
        "f2f0": 1,
        "f2f8": {"f06": 0, "f00": -1.0},
        "f2f4": 0,
        "f304": 1,
        "f30c": {"f06": 0, "f00": -1.0},
        "f308": 0,
        "f300": 0,
        "f314": 0,
        "f334": -1,
        "f338": -1,
        "has_f4a0": 0,
        "f318": 1,
        "f31c": 0,
        "f320": {"f06": 0, "f00": -1.0},
        "f328": 0,
        "f32c": 0,
        "has_f4b8": 0,
        "f6a0": _dimension_text(angular=angular),
        "f870": 1,
        "f874": 1,
        "f878": 0,
        "f7f8": "",
        "f800": "",
        "f818": "",
        "f820": "",
        "f880": _point(x=1.0),
        "f8a8": 0.5,
        "f8b0": 0.0,
        "f950": 0.0,
        "fa78": -1.0,
        "f958": _point(),
        "f970": _point(),
        "f988": _point(),
        "f9a0": _point(),
        "f9b8": _point(),
        "has_fa50": 0,
        "f898": 0,
        "f89c": 0,
        "f8a0": 0,
        "f8c0": 5,
        "f8e4": 2,
        "f8ec": 2,
        "f8f4": 2,
        "fa38": _point(),
        "f580": None,
        "f588": None,
        "f5a0": 0.0,
        "f5a8": 0.0,
        "has_f590": 0,
        "has_f598": 0,
        "f8e8": 2,
        "f8f0": 2,
        "f8a4": 0x427 | 0x80000000,
        "has_fa58": 0,
        "has_fa60": 0,
        "fa70": "",
        "faf8": None,
        "fb00": None,
        "f8f8": -1,
        "fad0": 0.0,
        "f5b0": {"elem": 8, "alloc_a": 16, "alloc_b": 1, "n": 1, "data": pack("<d", 0.0)},
        "f680": "",
        "f688": Obj("moFavoriteHandle_c", {"f08": 0, "f0c": -1, "f10": 0}),
        "fb40": -1.0,
        "fb68": 4,
        "fb6c": 0xFFFF,
        "fb60": ((0xFC | 0x20001 | (0x100 if design_intent else 0)) & 0xFDFFFFFF) | 0xE0E04000,
        "f830": 0.0,
        "f838": 0.0,
        "f840": 0.0,
        "f848": 0.0,
        "faf4": 0,
        "f8b8": -25.0,
        "f8fc": 1,
        "f900": 0,
        "f5c0": _raw_identity_transform(),
        "f648": 1.0,
        "fb70": "",
        "fb78": "",
        "fb80": "",
        "fb88": "",
        "fe48": empty_object_list(),
        "f908": empty_object_list(),
        "fb9c": -1,
        "fe40": 0,
        "fa80": None,
        "fa88": None,
        "fba0": None,
        "fb64": ((0x1870 & 0xFFFFFEF7) | 0x80205 | 0x30000 | 0x44000),
        "fab0": None,
        "fab8": None,
        "has_fac0": 0,
        "has_fac8": 0,
        "fa90": 0,
        "fef8": None,
        "fb4c": 1,
        "fb50": 1,
        "fd78": 0,
        "fd7c": 0,
        "ff00": 0,
        "f8c8": 0.0,
        "f8d0": 0,
        "ff08": 0,
        "ff0c": 0,
        "ff10": 0,
        "f8d8": 0,
        "f8dc": 0,
        "f808": "",
        "f810": "",
        "fd80": -1,
        "ff84": 0,
        "ff54": 0,
        "ff60": "",
        "f650": 0,
        "ff80": selected_leader,
        "ff68": _point(),
        "ff58": 0,
        "f8e0": 0,
        "ff88": "",
    })
    fields["f4f0"] = tuple({"p": _point()} for _ in range(4))
    fields["f550"] = tuple({"v": _point(y=1.0)} for _ in range(2))
    fields["f850"] = ({"o": handle},)
    return fields


def _display_fields(*, handle: Obj, angular: bool, design_intent: bool, selected_leader: int):
    fields = common_display_fields(handle=handle, angular=angular, design_intent=design_intent, selected_leader=selected_leader)
    if angular:
        fields.update({"f100c": 0, "f1010": 1, "f1008": 1, "ffb8": _point(x=1.0), "ffd0": _point(y=1.0), "ffe8": 0.1, "fff0": 0.9, "fff8": 0.1, "f1000": 0.9, "f1018": 0x18})
    else:
        fields.update({"f1014": 0, "ffb8": 0.0, "ffc0": 0.0, "ffe8": _point(), "f1000": 0, "f1008": None, "f1010": 0})
    return fields


@dataclass(frozen=True, kw_only=True)
class DimensionGraph:
    parameter: Obj
    dimension: Obj
    handle: Obj
    display: Obj


def feature_dimension(*, feature: Obj, dimension_id: int, value: float, angular: bool, allocator, design_intent: bool, selected_leader: int):
    from builders.Model import component_reference_fields, node_fields

    if not isinstance(feature, Obj) or feature.cls != "moExtrusion_c" or type(feature.get("f08")) is not int or feature["f08"] < 0:
        raise ConstructionError("feature dimensions require their allocated extrusion owner")
    if type(dimension_id) is not int or not 1 <= dimension_id < (1 << 31):
        raise ConstructionError("feature dimension numbers must be positive signed 32-bit integers")
    if type(angular) is not bool or type(design_intent) is not bool:
        raise ConstructionError("dimension kind and design intent must be semantic booleans")
    if type(selected_leader) is not int or not -(1 << 31) <= selected_leader < (1 << 31):
        raise ConstructionError("selected leader requires an explicit signed 32-bit presentation value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ConstructionError("feature dimension values must be finite numeric inputs")
    if angular and value != 0:
        raise ConstructionError("blind construction currently requires zero draft angles")
    if not angular and (value < 0 or 0 < value < 1e-14):
        raise ConstructionError("native length dimensions require zero or a positive value of at least 1e-14")
    parameter = Obj("moAngleParameter_c" if angular else "moLengthParameter_c")
    node_fields(name=f"D{dimension_id}", allocator=None, node=parameter)
    parameter.f.update({"_owner": feature, "f0c": 0, "f48": None, "f58": float(value), "f68": 0})
    fields = dimension_fields()
    fields.update({"_owner": feature, "f28": parameter, "f80": _point(), "fa0": _point(), "fc0": _point(), "has_fe0": 0, "has_ff0": 0, "pt_flags": 0, "_handles": []})
    del fields["refcount"]
    fields = DerivedFields(fields=fields, derived={"refcount": lambda: len(fields["_handles"])})
    dimension = Obj("AngleDim_c" if angular else "ParallelPlaneDistanceDim_c", fields)
    allocator.allocate(dimension, field="f50")
    if angular:
        dimension["ff8"] = 1
    handle_fields = component_reference_fields(component=None)
    handle_fields.update({"_owner": feature, "has_f120": 0, "f130": None, "f138": None, "f140": None, "f148": None, "f150": 0, "fe8": None, "f100": None, "f154": -1, "has_f128": 0, "f118": 0, "ff0": dimension})
    handle = Obj("moFeatureDimHandle_c", handle_fields)
    dimension["_handles"].append(handle)
    display = Obj("moDisplayAngularDim_c" if angular else "moDisplayDistanceDim_c", _display_fields(handle=handle, angular=angular, design_intent=design_intent, selected_leader=selected_leader))
    display["_owner"] = feature
    return DimensionGraph(parameter=parameter, dimension=dimension, handle=handle, display=display)


def _driving_value(*, display: Obj, angular: bool):
    expected = "moDisplayAngularDim_c" if angular else "moDisplayDistanceDim_c"
    if not isinstance(display, Obj) or display.cls != expected:
        raise ConstructionError(f"end specifications require an actual {expected} node")
    handles = display.get("f850")
    if not isinstance(handles, (tuple, list)) or len(handles) != 1:
        raise ConstructionError("display dimension f850 must contain one constructed model-dimension handle")
    if not isinstance(handles[0], Mapping):
        raise ConstructionError("display dimension handle entries require an object-reference mapping")
    handle = handles[0].get("o")
    if not isinstance(handle, Obj) or handle.cls != "moFeatureDimHandle_c":
        raise ConstructionError("display dimension f850[0].o must reference moFeatureDimHandle_c")
    if handle.get("fe8") is not None or handle.get("f100") is not None:
        raise ConstructionError("fresh feature-dimension handles require the local dimension branch")
    dimension = handle.get("ff0")
    expected_dimension = "AngleDim_c" if angular else "ParallelPlaneDistanceDim_c"
    if not isinstance(dimension, Obj) or dimension.cls != expected_dimension:
        raise ConstructionError(f"blind end dimension handle ff0 requires {expected_dimension}")
    parameter = dimension.get("f28")
    expected_parameter = "moAngleParameter_c" if angular else "moLengthParameter_c"
    if not isinstance(parameter, Obj) or parameter.cls != expected_parameter:
        raise ConstructionError(f"driving dimension f28 requires {expected_parameter}")
    value = parameter.get("f58")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ConstructionError("driving parameter f58 requires a finite numeric value")
    return float(value)


def modeled_end_spec(*, forward_distance: Obj, reverse_distance: Obj, forward_draft: Obj, reverse_draft: Obj, condition: str, reverse_direction: bool):
    if condition not in ("blind", "mid_plane", "two_directions") or type(reverse_direction) is not bool:
        raise ConstructionError("end specification requires a proven termination and explicit reversal")
    values = (forward_distance, reverse_distance, forward_draft, reverse_draft)
    if len({id(value) for value in values}) != len(values):
        raise ConstructionError("fresh end-spec dimensions require four distinct display nodes")
    depth = _driving_value(display=forward_distance, angular=False)
    reverse = _driving_value(display=reverse_distance, angular=False)
    if depth <= 0 or reverse <= 0 or condition != "two_directions" and reverse != depth:
        raise ConstructionError("end specifications require positive depths and matching inactive constructor depths")
    if _driving_value(display=forward_draft, angular=True) != 0 or _driving_value(display=reverse_draft, angular=True) != 0:
        raise ConstructionError("blind construction currently requires zero draft angles")
    return Obj("moEndSpec_c", {
        "f138": None,
        "f08": int(condition != "two_directions"),
        "f88": 0,
        "f8c": int(reverse_direction),
        "f90": None,
        "f0c": 6 if condition == "mid_plane" else 0,
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


def blind_end_spec(*, forward_distance: Obj, reverse_distance: Obj, forward_draft: Obj, reverse_draft: Obj):
    return modeled_end_spec(forward_distance=forward_distance, reverse_distance=reverse_distance, forward_draft=forward_draft, reverse_draft=reverse_draft, condition="blind", reverse_direction=False)


def require_blind_profile(profile):
    if not isinstance(profile, ProfileGraph) or profile.profile.cls != "moProfileFeature_c":
        raise ConstructionError("blind construction requires an ordinary constructed profile")
    if profile.point_count >= 3 and profile.line_count == profile.point_count and profile.arc_count == 0:
        return
    sketch = profile.sketch
    if sketch.get("_profile_kind") == "closed_curve":
        boundary = sketch.get("_closed_boundary", ())
        segments = (*sketch["_line_nodes"], *sketch["_arc_nodes"])
        if profile.point_count != 6 or profile.line_count != 2 or profile.arc_count != 2 or len(boundary) != 4:
            raise ConstructionError("mixed blind construction requires the modeled capsule boundary")
        if len({id(node) for node in boundary}) != 4 or {id(node) for node in boundary} != {id(node) for node in segments}:
            raise ConstructionError("closed boundary must own every actual line and arc exactly once")
        for index, node in enumerate(boundary):
            if node.get("_sketch") is not sketch or node.get("ext") is not None or node["_end"] is not boundary[(index + 1) % len(boundary)]["_start"]:
                raise ConstructionError("mixed blind construction requires an actual closed local endpoint ring")
            if node.cls == "sgArc" and (not node.get("_ordinary_arc") or node.get("_ordinary_circle") or node["fd8"] != 1 or node["fe0"] != -2):
                raise ConstructionError("capsule boundary requires its ordinary positive semicircular arcs")
        if len({id(node["_start"]) for node in boundary}) != 4:
            raise ConstructionError("capsule boundary vertices must be distinct actual points")
        return
    if sketch.get("_profile_kind") != "circle" or profile.point_count != 2 or profile.line_count != 0 or profile.arc_count != 1:
        raise ConstructionError("blind construction admits only the modeled closed polygon or single circle")
    arc = sketch["_arc_nodes"][0]
    fixed = sketch.get("_fixed_center")
    dimensions = sketch.get("_radial_dimensions", ())
    if arc["_start"] is not arc["_end"] or arc["_center"] is arc["_start"] or arc["_sketch"] is not sketch:
        raise ConstructionError("circle extrusion requires the actual closed local circle topology")
    if not isinstance(fixed, Obj) or fixed.cls != "sgLogG1Dim" or fixed["f80"] != 0x11 or fixed["h1"].get("_point") is not arc["_center"]:
        raise ConstructionError("circle extrusion requires its constructed fixed-center relation")
    if len(dimensions) != 1 or dimensions[0].cls != "sgCircleDim" or dimensions[0]["f80"] not in (3, 15) or dimensions[0]["h1"].get("_arc") is not arc or dimensions[0]["f68"] != 0:
        raise ConstructionError("circle extrusion requires its actual driving radial dimension")


def profile_extrusion(*, feature: Obj, profile: ProfileGraph, end_spec: Obj, depth: float):
    if not isinstance(feature, Obj) or feature.cls != "moExtrusion_c":
        raise ConstructionError("blind extrusion requires an allocated moExtrusion_c body-feature node")
    for name in ("f08", "f28", "f60", "f368", "f388", "f780"):
        if name not in feature.f:
            raise ConstructionError(f"body-feature factory has not constructed required base field {name}")
    if type(feature["f08"]) is not int or feature["f08"] < 0 or type(feature["f28"]) is not int:
        raise ConstructionError("body-feature identifiers and flags must come from the allocated model factory node")
    require_blind_profile(profile)
    if not isinstance(end_spec, Obj) or end_spec.cls != "moEndSpec_c" or type(end_spec.get("f08")) is not int or end_spec["f08"] not in (0, 1) or end_spec.get("f0c") not in (0, 6) or end_spec.get("f10") != 0 or end_spec.get("f88") != 0 or type(end_spec.get("f8c")) is not int or end_spec["f8c"] not in (0, 1):
        raise ConstructionError("extrusion requires a modeled blind, mid-plane or two-direction end specification")
    if end_spec["f0c"] == 6 and end_spec["f08"] != 1:
        raise ConstructionError("mid-plane construction requires a single full-depth parameter")
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


def blind_extrusion(*, feature: Obj, profile: ProfileGraph, end_spec: Obj, depth: float):
    if not isinstance(end_spec, Obj) or end_spec.get("f08") != 1 or end_spec.get("f0c") != 0 or end_spec.get("f8c") != 0:
        raise ConstructionError("legacy blind construction requires forward single-ended semantics")
    return profile_extrusion(feature=feature, profile=profile, end_spec=end_spec, depth=depth)


@dataclass(frozen=True, kw_only=True)
class ExtrusionGraph:
    feature: Obj
    profile: ProfileGraph
    end_spec: Obj
    dimensions: tuple[DimensionGraph, ...]
    from_offset: DimensionGraph

    @property
    def dimension_count(self):
        return len(self.dimensions)

    @property
    def constructed_dimensions(self):
        return (*self.dimensions, self.from_offset)

    @property
    def parameters(self):
        return tuple(item.parameter for item in self.dimensions)

    @property
    def displays(self):
        return tuple(item.display for item in self.dimensions)

    @property
    def depth(self):
        return self.dimensions[0].parameter["f58"]


    @property
    def condition(self):
        return "mid_plane" if self.end_spec["f0c"] == 6 else "two_directions" if self.end_spec["f08"] == 0 else "blind"

    @property
    def reverse_direction(self):
        return bool(self.end_spec["f8c"])

    @property
    def reverse_depth(self):
        return self.dimensions[1].parameter["f58"] if self.end_spec["f08"] == 0 else None

    @property
    def active_distances(self):
        return self.dimensions[:2 if self.end_spec["f08"] == 0 else 1]


def live_extrusion(*, feature: Obj, profile: ProfileGraph, depth: float, allocator, design_intent: bool, selected_leader: int, condition: str, reverse_direction: bool, reverse_depth: float | None = None):
    if not isinstance(feature, Obj) or feature.cls != "moExtrusion_c":
        raise ConstructionError("live blind construction requires a body-feature factory extrusion node")
    require_blind_profile(profile)
    if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not isfinite(depth) or depth < 1e-14:
        raise ConstructionError("native blind construction requires a finite depth of at least 1e-14 metres")
    if type(design_intent) is not bool or type(selected_leader) is not int or not -(1 << 31) <= selected_leader < (1 << 31):
        raise ConstructionError("live blind construction requires explicit design intent and selected-leader presentation inputs")
    if condition not in ("blind", "mid_plane", "two_directions") or type(reverse_direction) is not bool:
        raise ConstructionError("live extrusion requires a proven end condition and explicit reversal")
    if condition == "two_directions":
        if isinstance(reverse_depth, bool) or not isinstance(reverse_depth, (int, float)) or not isfinite(reverse_depth) or reverse_depth < 1e-14:
            raise ConstructionError("second direction requires its independent positive finite depth")
        second_depth = reverse_depth
    else:
        if reverse_depth is not None:
            raise ConstructionError("single-ended extrusion cannot supply a second active depth")
        second_depth = depth
    dimensions = tuple(feature_dimension(feature=feature, dimension_id=i + 1, value=(depth, second_depth, 0.0, 0.0)[i], angular=i >= 2, allocator=allocator, design_intent=design_intent, selected_leader=selected_leader) for i in range(4))
    from_offset = feature_dimension(feature=feature, dimension_id=19, value=0.0, angular=False, allocator=allocator, design_intent=design_intent, selected_leader=selected_leader)
    end_spec = modeled_end_spec(forward_distance=dimensions[0].display, reverse_distance=dimensions[1].display, forward_draft=dimensions[2].display, reverse_draft=dimensions[3].display, condition=condition, reverse_direction=reverse_direction)
    end_spec["f140"]["f28"] = from_offset.display
    profile_extrusion(feature=feature, profile=profile, end_spec=end_spec, depth=depth)
    return ExtrusionGraph(feature=feature, profile=profile, end_spec=end_spec, dimensions=dimensions, from_offset=from_offset)


def live_blind_extrusion(*, feature: Obj, profile: ProfileGraph, depth: float, allocator, design_intent: bool, selected_leader: int):
    return live_extrusion(feature=feature, profile=profile, depth=depth, allocator=allocator, design_intent=design_intent, selected_leader=selected_leader, condition="blind", reverse_direction=False)
