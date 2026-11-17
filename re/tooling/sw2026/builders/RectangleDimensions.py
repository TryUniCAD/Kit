from __future__ import annotations

from collections import Counter
from math import isfinite
from struct import pack

from Core import Obj
from builders.Extrude import DimensionGraph, _point, common_display_fields
from builders.Model import PersistentIds, component_reference_fields, node_fields
from builders.Sketch import ConstructionError, DerivedFields, NodeOrder, ProfileGraph, _vector, dimension_fields, line_handle, point_handle


def _rectangle_edges(*, graph):
    if not isinstance(graph, ProfileGraph) or graph.profile.cls != "moProfileFeature_c":
        raise ConstructionError("rectangle dimensions require an ordinary polygon profile")
    if graph.sketch is not graph.profile["pd_f80"]:
        raise ConstructionError("rectangle dimensions require the sketch owned by the supplied profile")
    frame = graph.profile["_frame"]
    if (frame.origin, frame.u, frame.v) != ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)):
        raise ConstructionError("rectangle dimensions require the origin Front Plane frame")
    points = graph.sketch.get("_point_nodes")
    lines = graph.sketch.get("_line_nodes")
    if not isinstance(points, NodeOrder) or not isinstance(lines, NodeOrder) or len(points) != 4 or len(lines) != 4:
        raise ConstructionError("rectangle dimensions require four local point and line roles")
    positions = tuple((point["pos"]["x"], point["pos"]["y"]) for point in points)
    (left, bottom), (right, top) = positions[0], positions[2]
    if not left < right or not bottom < top or positions[1] != (right, bottom) or positions[3] != (left, top):
        raise ConstructionError("rectangle points must run counterclockwise from the lower-left corner")
    for index, line in enumerate(lines):
        if line.cls != "sgLine" or line["_start"] is not points[index] or line["_end"] is not points[(index + 1) % len(points)]:
            raise ConstructionError("rectangle lines must join consecutive local point roles")
    return points, lines


def _logical_axis(*, sketch, line, lines, horizontal):
    fields = dimension_fields()
    fields.update({
        "_sketch": sketch,
        "f80": 4 if horizontal else 5,
        "f90": 2, "f94": 0, "f98": 0, "fa0": 0xFFFE, "fa4": 0,
        "h1": line_handle(sketch=sketch, line=line, lines=lines),
    })
    return Obj("sgLogG1Dim", fields)


def _length_dimension(*, graph, points, line, ordinal, length):
    parameter = Obj("moLengthParameter_c")
    node_fields(name=f"D{ordinal}", allocator=None, node=parameter)
    parameter.f.update({"_owner": graph.profile, "f0c": 0, "f48": None, "f58": length, "f68": 0})
    fields = dimension_fields()
    fields.update({
        "_owner": graph.profile, "_sketch": graph.sketch, "_ordinary_rectangle_value": True,
        "f28": parameter, "f80": 1, "f90": 2, "f94": 0, "f98": 0, "fa0": 0,
        "h1": point_handle(sketch=graph.sketch, point=line["_start"], points=points),
        "h2": point_handle(sketch=graph.sketch, point=line["_end"], points=points),
        "f180": 1, "f184": 1, "f1b8": 1, "f1bc": 0,
        "plane": None, "dir": _point(),
    })
    return Obj("sgPntPntDist", fields)


def _handle(*, sketch, dimension, values):
    fields = component_reference_fields(component=None)
    fields.update({
        "has_f120": 0, "has_f128": 0, "f130": None, "f138": None,
        "f140": None, "f148": None, "f150": 0, "fe8": None,
        "f100": None, "f154": -1, "f118": 0, "ff0": sketch,
    })
    return Obj("moSkDimHandleValG2_c", DerivedFields(fields=fields, derived={
        "ff8": lambda: values.index_of(node=dimension),
    }))


def _linear_style(*, fields, detail):
    style = detail["fe0"]
    if style["f44"] != 0 or detail["fd8"] & 2:
        raise ConstructionError("rectangle dimensions require the ordinary zero-tolerance, freely placed text style")
    fields.update({
        "f870": detail["f6c"], "f874": detail["f6c"], "f8ec": style["f84"],
        "fb68": style["fc"], "fb6c": style["f10"], "ff00": detail["fc0"], "fe40": style["f08"],
        "ff10": int(bool(style["fe0"] & 0x10000)),
        "f30c": dict(style["fd0"]["f10"]), "f320": dict(style["fd8"]["f10"]),
    })
    under_text = fields["f8f4"] != 1 and (fields["f8f4"] != 2 or detail["f74"] == 0) and detail["f60"] == 0
    fields["f8a4"] = (fields["f8a4"] & ~0x50) | (0x40 if under_text else 0) | 0x2000000
    flags = ((0x100000 if detail["fd8"] & 0x100000 else 0)
             | (0x1000 if style["f78"] else 0)
             | (0x2000 if style["f9c"] else 0))
    fields["fb64"] = (fields["fb64"] & ~0x103000) | flags


def _display(*, profile, length, line, handle, annotation_id, text_point, horizontal, design_intent, selected_leader, route_centerline):
    fields = common_display_fields(handle=handle, angular=False, design_intent=design_intent, selected_leader=selected_leader)
    _linear_style(fields=fields, detail=profile["owner"]["fae0"]["f13b0"])
    start = line["_start"]["pos"]
    end = line["_end"]["pos"]
    x, y = _vector(value=text_point, size=2)
    if horizontal:
        direction = _point(x=1.0)
        witness = _point(y=-1.0)
        along, away = x - start["x"], start["y"] - y
    else:
        direction = _point(y=1.0)
        witness = _point(x=1.0)
        along, away = y - start["y"], x - start["x"]
    if not 0.0 <= along <= length or not isfinite(away) or away <= 0.0:
        raise ConstructionError("dimension text must lie outside the rectangle beside its dimensioned edge")
    fields["f6a0"]["f38"] = _point(x=x, y=y)
    fields["f6a0"]["f10"] = 0x12
    fields["f5b0"]["data"] = pack("<d", length)
    first_model_point = _point(x=start["x"], y=start["y"])
    second_model_point = _point(x=end["x"], y=end["y"])
    fields.update({
        "_owner": profile, "f58": annotation_id,
        "f880": witness, "f8a8": along / length, "f8b0": away,
        "f958": first_model_point, "f970": dict(first_model_point),
        "f988": second_model_point, "f9a0": dict(second_model_point),
        "fa38": direction, "fad0": length,
        "f1014": 0x800 if route_centerline else 0,
        "ffb8": 0.0, "ffc0": 0.0, "ffe8": _point(), "f1000": 0, "f1008": None, "f1010": 0,
    })
    return Obj("moDisplayDistanceDim_c", fields)


def rectangle_dimensions(*, graph, width_text_m, height_text_m, allocator, design_intent, selected_leader, route_centerline):
    points, lines = _rectangle_edges(graph=graph)
    if not isinstance(allocator, PersistentIds) or type(route_centerline) is not bool:
        raise ConstructionError("rectangle dimensions require the model allocator and an explicit dimension routing preference")
    sketch = graph.sketch
    dims = sketch["dims"]
    if any(dims[name] for name in ("val_g1", "val_g2", "val_g3", "log_g1", "log_g2", "log_g3")) or dims["f118"]["items"]:
        raise ConstructionError("rectangle dimensions require a fresh sketch without prior dimensions or relations")
    entities = (*points, *lines)
    if any(entity["f20"] for entity in entities):
        raise ConstructionError("rectangle dimensions require unused local points and lines")
    model = graph.profile["owner"]
    annotation_id = model["fd44"]
    if type(annotation_id) is not int or not 0 < annotation_id <= 0x7FFFFFFD:
        raise ConstructionError("model annotation id counter cannot allocate two signed entries")
    width = points[1]["pos"]["x"] - points[0]["pos"]["x"]
    height = points[2]["pos"]["y"] - points[1]["pos"]["y"]
    if not all(isfinite(length) and length > 1e-8 for length in (width, height)):
        raise ConstructionError("rectangle dimensions require finite lengths above the native display tolerance")
    lengths = (width, height)
    values = NodeOrder(nodes=(
        _length_dimension(graph=graph, points=points, line=lines[index], ordinal=index + 1, length=length)
        for index, length in enumerate(lengths)
    ))
    graphs = []
    for index, (dimension, placement, length) in enumerate(zip(values, (width_text_m, height_text_m), lengths, strict=True)):
        handle = _handle(sketch=sketch, dimension=dimension, values=values)
        display = _display(
            profile=graph.profile, length=length, line=lines[index], handle=handle,
            annotation_id=annotation_id + index, text_point=placement, horizontal=index == 0,
            design_intent=design_intent, selected_leader=selected_leader, route_centerline=route_centerline,
        )
        graphs.append(DimensionGraph(parameter=dimension["f28"], dimension=dimension, handle=handle, display=display))

    logical = tuple(
        _logical_axis(sketch=sketch, line=line, lines=lines, horizontal=index % 2 == 0)
        for index, line in enumerate(lines)
    )
    reference_counts = Counter(dim["h1"]["_line"] for dim in logical)
    reference_counts.update(dim[handle]["_point"] for dim in values for handle in ("h1", "h2"))
    for value in values:
        allocator.allocate(value, field="f50")
    for entity in entities:
        entity["f20"] = reference_counts[entity]
    model["fd44"] = annotation_id + len(graphs)
    dims["log_g1"].extend({"d": logical_dim.f} for logical_dim in logical)
    dims["val_g2"].extend({"d": dimension} for dimension in values)
    dims["f118"]["items"].extend({"o": result.display} for result in graphs)
    return tuple(graphs)
