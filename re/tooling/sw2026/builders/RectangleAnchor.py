from __future__ import annotations

from Core import Obj
from builders.Model import component_reference_fields, reference_wrapper_fields
from builders.Sketch import ConstructionError, NodeOrder, dimension_fields, line_handle, ordinary_line, ordinary_point, point_handle


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


def coincident_relation(*, first, second):
    for handle in (first, second):
        entity = handle["_point"] if handle.cls == "sgPointHandle" else handle["_line"]
        entity["f20"] += 1
    return {
        **dimension_fields(),
        "f80": 9, "f90": 2, "f94": 0, "f98": 0, "fa0": 0xFFFE, "fa4": 0, "h1": first, "h2": second,
        "ff8": 0, "ffc": 0, "f108": None, "f100": 0, "f110": -1, "f114": -1, "f118": 0.0,
        "f120": 0.0, "ext1": None, "ext2": None, "ext3": None, "f150": 0, "f154": -1,
    }


def centered_diagonals(*, sketch, corners, contour):
    opposite_corners = ((corners[0], corners[2]), (corners[1], corners[3]))
    if any(first["pos"][axis] != -second["pos"][axis] for first, second in opposite_corners for axis in ("x", "y")):
        raise ConstructionError("a center anchor requires two actual diagonals meeting at the authored origin")
    center = ordinary_point(sketch=sketch, position=(0.0, 0.0))
    center["fe4"] = 1
    center["f0c"] = len(corners) + 1
    points = NodeOrder(nodes=(*corners, center))
    diagonals = tuple(ordinary_line(sketch=sketch, start=start, end=end, points=points) for start, end in opposite_corners)
    for ordinal, diagonal in enumerate(diagonals, start=len(contour) + 1):
        diagonal["f54"] |= 8
        diagonal["f0c"] = ordinal
        for key in ("_start", "_end"):
            point = diagonal[key]
            point.f.derived["fe8"] = lambda node=point: sum(node is segment[key] for segment in (*contour, *diagonals)
                                                           for key in ("_start", "_end"))
    lines = NodeOrder(nodes=(*contour, *diagonals))
    records = (*sketch["lines"], *({"flags": 2, "line": line.f} for line in diagonals))
    sketch.f.derived["lines"] = lambda: records
    sketch.f.derived["f56c"] = lambda: len(lines) + 1
    sketch["f140"].derived["f0c"] = lambda: len(lines) + 1
    sketch["_line_nodes"] = lines
    relations = tuple(coincident_relation(first=point_handle(sketch=sketch, point=center, points=points),
                                          second=line_handle(sketch=sketch, line=line, lines=lines)) for line in diagonals)
    return center, points, relations


def rectangle_origin(*, graph, origin, component, origin_created_at, mode):
    sketch = graph.sketch
    dims = sketch["dims"]
    corners, contour = graph.points, graph.lines
    if len(corners) != 4 or len(contour) != 4 or len(dims["val_g2"]) != 2 or dims["log_g2"]:
        raise ConstructionError("an origin anchor requires the ordinary dimensioned rectangle")
    if graph.profile["_frame"] != origin.profile["_frame"] or len(origin.points) != 1:
        raise ConstructionError("an origin anchor requires the document's native Front Plane frame")
    if mode == "corner":
        local = corners[0]
        if local["pos"] != {"x": 0.0, "y": 0.0}:
            raise ConstructionError("an origin corner requires the authored first vertex at (0, 0)")
        local_points = corners
        point_records = sketch["points"]
        diagonal_relations = ()
    elif mode == "center":
        local, local_points, diagonal_relations = centered_diagonals(sketch=sketch, corners=corners, contour=contour)
        point_records = (*sketch["points"], {"kind": 0, "point": local.f})
    else:
        raise ConstructionError("unknown rectangle origin anchor mode")
    target, = origin.points
    external_fields = ordinary_point(sketch=sketch, position=(0.0, 0.0)).f
    external_fields.update(ext=origin_reference(origin=origin, target=target, component=component, created_at=origin_created_at),
                           fe4=6, f54=external_fields["f54"] & 0xFFFC, f0c=len(local_points) + 1)
    external = Obj("sgExternalPoint", external_fields)
    points = NodeOrder(nodes=(*local_points, external))
    relation = coincident_relation(first=point_handle(sketch=sketch, point=external, points=points),
                                   second=point_handle(sketch=sketch, point=local, points=points))
    records = (*point_records, {"kind": 1, "point": external.f})
    sketch.f.derived["points"] = lambda: records
    sketch["f140"].derived["f08"] = lambda: len(points) + 1
    sketch["_point_nodes"] = points
    sketch["_origin_anchor"] = (external, origin.profile, relation, diagonal_relations)
    dims["log_g2"].extend({"d": constraint} for constraint in (*diagonal_relations, relation))
    return external
