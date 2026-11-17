from __future__ import annotations

from Core import Obj
from builders.Model import component_reference_fields, reference_wrapper_fields
from builders.Sketch import ConstructionError, NodeOrder, dimension_fields, ordinary_point, point_handle


def origin_reference(*, origin, target, component, created_at):
    profile = origin.profile
    if profile.cls != "moOriginProfileFeature_c" or component["owner"] is not profile["owner"]:
        raise ConstructionError("rectangle anchor requires the document's own origin profile")
    if target["f0c"] != 1 or target["pos"] != {"x": 0.0, "y": 0.0}:
        raise ConstructionError("rectangle anchor requires the origin profile's first point")
    target["f08"] = target["f0c"]
    selected = Obj("moCompSketchEntHandle_c", {
        **component_reference_fields(component=component),
        "ff0": {"f00": profile["f08"], "f08": created_at},
        "f0f8": point_handle(sketch=origin.sketch, point=target, points=origin.sketch["_point_nodes"]),
        "f100": target["f08"],
    })
    point = origin.profile["_frame"].world_point(point=(target["pos"]["x"], target["pos"]["y"]))
    wrapper = Obj("moSketchExtRef_w", {
        **reference_wrapper_fields(reference=selected),
        "fb0": 0,
        "fb8": Obj("moPointBackedUpData_c", {"f08": dict(zip("xyz", point, strict=True))}),
    })
    return Obj("sgExtEnt_c", {
        "f08": wrapper, "f10": None, "f18": None, "f20": None,
        "f28": f"Point{target['f0c']}@{profile['f18']['f08']}",
    })


def corner_origin(*, graph, origin, component, origin_created_at):
    sketch = graph.sketch
    dims = sketch["dims"]
    if len(graph.points) != 4 or len(graph.lines) != 4 or len(dims["val_g2"]) != 2 or dims["log_g2"]:
        raise ConstructionError("an origin corner requires the ordinary dimensioned rectangle")
    corner = graph.points[0]
    if corner["pos"] != {"x": 0.0, "y": 0.0}:
        raise ConstructionError("an origin corner requires the authored first vertex at (0, 0)")
    if graph.profile["_frame"] != origin.profile["_frame"] or len(origin.points) != 1:
        raise ConstructionError("an origin corner requires the document's native Front Plane frame")
    target, = origin.points
    external_fields = ordinary_point(sketch=sketch, position=(0.0, 0.0)).f
    external_fields.update(ext=origin_reference(origin=origin, target=target, component=component, created_at=origin_created_at),
                           fe4=6, f54=external_fields["f54"] & 0xFFFC, f0c=len(graph.points) + 1)
    external = Obj("sgExternalPoint", external_fields)
    points = NodeOrder(nodes=(*graph.points, external))
    relation = {
        **dimension_fields(),
        "f80": 9, "f90": 2, "f94": 0, "f98": 0, "fa0": 0xFFFE, "fa4": 0,
        "h1": point_handle(sketch=sketch, point=external, points=points),
        "h2": point_handle(sketch=sketch, point=corner, points=points),
        "ff8": 0, "ffc": 0, "f108": None, "f100": 0, "f110": -1, "f114": -1, "f118": 0.0,
        "f120": 0.0, "ext1": None, "ext2": None, "ext3": None, "f150": 0, "f154": -1,
    }
    for handle in (relation["h1"], relation["h2"]):
        handle["_point"]["f20"] += 1
    records = (*sketch["points"], {"kind": 1, "point": external.f})
    sketch.f.derived["points"] = lambda: records
    sketch["f140"].derived["f08"] = lambda: len(points) + 1
    sketch["_point_nodes"] = points
    sketch["_corner_origin"] = (external, origin.profile, relation)
    dims["log_g2"].append({"d": relation})
    return external
