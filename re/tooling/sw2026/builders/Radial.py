from __future__ import annotations

from math import isfinite, sqrt
from struct import pack

from Core import Obj
from builders.Circle import arc_handle
from builders.Extrude import DimensionGraph, _point, common_display_fields
from builders.Model import component_reference_fields, node_fields
from builders.Sketch import ConstructionError, DerivedFields, NodeOrder, _node_index, _vector, dimension_fields, logical_point_constraint


def assign_bit(value, mask, enabled):
    return (value & ~mask) | (mask if enabled else 0)


def parameter_node(*, profile, value):
    parameter = Obj("moLengthParameter_c")
    node_fields(name="D1", allocator=None, node=parameter)
    parameter.f.update({"_owner": profile, "f0c": 0, "f48": None, "f58": value, "f68": 0})
    return parameter


def value_dimension(*, profile, parameter, arc, arcs, diameter, allocator):
    sketch = profile["pd_f80"]
    fields = dimension_fields()
    fields.update({
        "_owner": profile, "_sketch": sketch, "f28": parameter,
        "f80": 15 if diameter else 3, "f90": 2, "f94": 0, "f98": 0,
        "fa0": 0, "g1": 0, "g2": 0, "dir": _point(x=1.0),
        "h1": arc_handle(sketch=sketch, arc=arc, arcs=arcs),
        "h2": Obj("sgEntHandle", {"_sketch": None, "idx": 0x777F, "f18": -2, "f1c": -1, "f08": 0}),
        "_ordinary_circle_value": True,
    })
    dimension = Obj("sgCircleDim", fields)
    allocator.allocate(dimension, field="f50")
    return dimension


def display_handle(*, sketch, dimension, values):
    fields = component_reference_fields(component=None)
    fields.update({
        "has_f120": 0, "has_f128": 0, "f130": None, "f138": None,
        "f140": None, "f148": None, "f150": 0, "fe8": None,
        "f100": None, "f154": -1, "f118": 0, "ff0": sketch,
        "_value_dimension": dimension,
    })
    return Obj("moSkDimHandleRadial_c", DerivedFields(fields=fields, derived={
        "ff8": lambda: _node_index(nodes=values, node=dimension),
    }))


def projected_style(*, fields, root, subtype, diameter):
    for name, value in (("f870", root["f6c"]), ("f874", root["f6c"]), ("fb68", subtype["fc"]), ("fb6c", subtype["f10"]), ("f8ec", subtype["f84"])):
        if type(value) is not int or not 0 <= value <= 0xFFFF:
            raise ConstructionError(f"radial style {name} must fit its native wire width")
        fields[name] = value
    if subtype["f44"] != 0:
        raise ConstructionError("radial construction does not admit a tolerance style")
    under = False if fields["f8f4"] == 1 or fields["f8f4"] == 2 and root["f74"] != 0 else root["f60"] == 0
    fields["f8a4"] = assign_bit(fields["f8a4"], 0x40, under)
    fields["f8a4"] = assign_bit(fields["f8a4"], 0x10, bool(root["fd8"] & 2))
    fields["fb64"] = assign_bit(fields["fb64"], 0x100000, bool(root["fd8"] & 0x100000))
    fields["fb64"] = assign_bit(fields["fb64"], 0x1000, subtype["f78"] != 0)
    fields["fb64"] = assign_bit(fields["fb64"], 0x2000, subtype["f9c"] != 0)
    fields["ff00"] = root["fc0"]
    fields["ff10"] = int(bool(subtype["fe0"] & 0x10000))
    fields["fe40"] = subtype["f08"]
    fields["f30c"] = dict(subtype["fd0"]["f10"])
    fields["f320"] = dict(subtype["fd8"]["f10"])
    solid = subtype["f104"] & 2 == 0 if diameter else subtype["f100"] & 4 == 0
    fields["ffd8"] = assign_bit(fields["ffd8"], 4, solid)
    if fields["f8a4"] & 0x10:
        raise ConstructionError("radial construction requires the explicit center-text style to be disabled")


def radial_display(*, profile, handle, parameter, mode, text_point_m, design_intent, selected_leader):
    frame = profile["_frame"]
    if frame.origin != (0.0, 0.0, 0.0) or frame.u != (1.0, 0.0, 0.0) or frame.v != (0.0, 1.0, 0.0):
        raise ConstructionError("the first radial presentation rung requires the canonical front-plane frame")
    point = _vector(value=text_point_m, size=3)
    if point[2] != 0.0:
        raise ConstructionError("radial text must lie in the admitted sketch plane")
    diameter = mode == "diameter"
    fields = common_display_fields(handle=handle, angular=False, design_intent=design_intent, selected_leader=selected_leader)
    fields.update({"ffd8": 0x80086, "ffd4": 0, "ffc0": [], "f1050": None, "f1048": "", "f1068": None, "has_f1060": 0, "f1090": None, "f10a8": None, "f10a4": 0})
    for name in ("ffe0", "ffe8", "fff0", "fff8", "f1000", "f1008"):
        fields[name] = 0.0
    fields["f1010"] = _point()
    fields["f1028"] = _point()
    fields.derived["nfc0"] = lambda: len(fields["ffc0"])
    fields["f6a0"]["f38"] = dict(zip(("x", "y", "z"), point, strict=True))
    fields["f6a0"]["f10"] = 0x11 if diameter else 0x14
    fields["fb64"] |= 0x800
    root = profile["owner"]["fae0"]["f13b0"]
    subtype = root["f960" if diameter else "f3f8"]
    projected_style(fields=fields, root=root, subtype=subtype, diameter=diameter)
    center = handle["_value_dimension"]["h1"]["_arc"]["_center"]["pos"]
    direction = (point[0] - center["x"], point[1] - center["y"], 0.0)
    squared = direction[0] * direction[0] + direction[1] * direction[1]
    center_squared = center["x"] * center["x"] + center["y"] * center["y"]
    if not isfinite(squared) or not isfinite(center_squared):
        raise ConstructionError("radial placement intermediates must be finite")
    distance = sqrt(squared)
    if max(abs(direction[0]), abs(direction[1])) >= 1e-8:
        if squared < 1e-17:
            raise ConstructionError("radial placement direction is below the admitted native unit-vector domain")
        fields["f880"] = dict(zip(("x", "y", "z"), (value / distance for value in direction), strict=True))
    value = parameter["f58"]
    radius = value / 2.0 if diameter else value
    if value > 1e-8:
        fields["f8a8"] = distance * (1.0 / radius)
        fields["f8b0"] = distance - radius
        if not isfinite(fields["f8a8"]) or not isfinite(fields["f8b0"]):
            raise ConstructionError("radial placement ratios must be finite")
    fields["fad0"] = sqrt(center_squared) if max(abs(center["x"]), abs(center["y"])) >= 1e-8 else value
    fields["f958"] = _point(x=center["x"], y=center["y"])
    fields["f988"] = _point(x=center["x"], y=center["y"])
    fields["f950"] = value
    fields["f5b0"]["data"] = pack("<d", value)
    fields["f3e0"] &= ~0x200
    fields["f8a4"] &= ~0x8000
    fields["ffd8"] = assign_bit(fields["ffd8"], 0x10, not diameter)
    fields["ffd8"] |= 0x100000
    fields["ffd8"] |= 0x200000
    fields["f7f8"] = "<MOD-DIAM>" if diameter else "R"
    fields["fb60"] |= 0x200
    fields["_owner"] = profile
    return Obj("moDisplayRadialDim_c", fields)


def fix_circle_center(*, graph):
    sketch = graph.sketch
    arc = sketch["_arc_nodes"][0]
    center = arc["_center"]
    if sketch["dims"]["log_g1"] or center["fe4"] != 0 or center["fe8"] != 1 or center["fec"] != 1 or center["f20"] != 0:
        raise ConstructionError("center fixation requires one unused ordinary center role")
    constraint = logical_point_constraint(sketch=sketch, point=center, points=sketch["_point_nodes"])
    sketch["dims"]["log_g1"].append({"d": constraint.f})
    center["_constraints"] = (constraint,)
    del center.f["f20"]
    center.f.derived["f20"] = lambda: len(center["_constraints"])
    sketch["_fixed_center"] = constraint
    return constraint


def circle_dimension(*, graph, mode, text_point_m, allocator, design_intent, selected_leader, fix_center=False):
    if mode not in ("radius", "diameter"):
        raise ConstructionError("circle dimension mode must be radius or diameter")
    if type(fix_center) is not bool:
        raise ConstructionError("circle center fixation must be an authored boolean")
    sketch = graph.sketch
    if sketch.get("_profile_kind") != "circle" or len(sketch["_arc_nodes"]) != 1 or sketch["dims"]["val_g1"] or sketch["dims"]["f118"]["items"]:
        raise ConstructionError("radial construction requires one fresh undimensioned local circle")
    arc = sketch["_arc_nodes"][0]
    center, marker = arc["_center"]["pos"], arc["_start"]["pos"]
    dx, dy = marker["x"] - center["x"], marker["y"] - center["y"]
    radius = sqrt(dx * dx + dy * dy)
    value = 2.0 * radius if mode == "diameter" else radius
    if not isfinite(value) or value <= 0:
        raise ConstructionError("circle dimension geometry must yield a finite positive value")
    if fix_center:
        fix_circle_center(graph=graph)
    parameter = parameter_node(profile=graph.profile, value=value)
    dimension = value_dimension(profile=graph.profile, parameter=parameter, arc=arc, arcs=sketch["_arc_nodes"], diameter=mode == "diameter", allocator=allocator)
    values = NodeOrder(nodes=(dimension,))
    sketch["dims"]["val_g1"].append({"d": dimension})
    arc["_constraints"] = (dimension,)
    del arc.f["f20"]
    arc.f.derived["f20"] = lambda: len(arc["_constraints"])
    handle = display_handle(sketch=sketch, dimension=dimension, values=values)
    display = radial_display(profile=graph.profile, handle=handle, parameter=parameter, mode=mode, text_point_m=text_point_m, design_intent=design_intent, selected_leader=selected_leader)
    displays = sketch["dims"]["f118"]
    displays["items"].append({"o": display})
    sketch["_radial_dimensions"] = (dimension,)
    sketch["_value_nodes"] = values
    return DimensionGraph(parameter=parameter, dimension=dimension, handle=handle, display=display)
