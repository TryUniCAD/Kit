from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite, tau
from struct import pack

from Core import Obj
from builders.Extrude import DimensionGraph, _construct_feature_dimension
from builders.Geometry import bind_arrays, bind_permanence
from builders.Model import component_reference_fields, logged_creation_time, node_list, reference_wrapper_fields
from builders.Sketch import ConstructionError, DerivedFields, NodeOrder, PlaneFrame, ProfileGraph, _bind_local_ref_flag, _vector, empty_object_list, line_handle, new_profile, ordinary_line, ordinary_point, polygon_vertices


@dataclass(frozen=True, kw_only=True)
class RevolveProfile:
    profile: ProfileGraph
    axis: Obj
    frame: PlaneFrame


@dataclass(frozen=True, kw_only=True)
class RevolutionGraph:
    feature: Obj
    axis_reference: Obj
    end: Obj
    angle: DimensionGraph


def revolved_profile(*, vertices, axis_start, axis_end, profile: Obj, plane: Obj, frame: PlaneFrame) -> RevolveProfile:
    if not isinstance(frame, PlaneFrame) or not isinstance(profile, Obj) or profile.cls != "moProfileFeature_c":
        raise ConstructionError("a revolved boss requires an allocated planar profile")
    corners = polygon_vertices(vertices=vertices)
    xs, ys = {x for x, _ in corners}, {y for _, y in corners}
    if len(corners) != 4 or len(xs) != 2 or len(ys) != 2 or set(corners) != {(x, y) for x in xs for y in ys}:
        raise ConstructionError("the ordinary revolved boss candidate requires an axis-aligned rectangular contour")
    start = _vector(value=axis_start, size=2)
    end = _vector(value=axis_end, size=2)
    if start[0] != end[0] or not start[0] < min(xs) or end[1] - start[1] < 1e-8:
        raise ConstructionError("the construction axis must be an upward line to the left of the closed contour")
    for position in (*corners, start, end):
        frame.world_point(point=position)
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    sketch = graph.sketch
    points = NodeOrder(nodes=(ordinary_point(sketch=sketch, position=position) for position in (*corners, start, end)))
    contour = tuple(ordinary_line(sketch=sketch, start=point, end=points[(index + 1) % len(corners)], points=points) for index, point in enumerate(points[:len(corners)]))
    axis = ordinary_line(sketch=sketch, start=points[-2], end=points[-1], points=points)
    axis["f54"] |= 8
    lines = NodeOrder(nodes=(*contour, axis))
    arcs = NodeOrder(nodes=())
    bind_permanence(sketch=sketch, points=points, lines=lines, arcs=arcs)
    bind_arrays(sketch=sketch, points=points, lines=lines, arcs=arcs)
    _bind_local_ref_flag(sketch=sketch)
    sketch["_requires_update"] = True
    return RevolveProfile(profile=graph, axis=axis, frame=frame)


def _point(values):
    return dict(zip("xyz", values, strict=True))


def _axis_reference(*, source: RevolveProfile, component: Obj, profile_created_at: int) -> Obj:
    profile, axis, frame = source.profile, source.axis, source.frame
    sketch = profile.sketch
    points = [frame.world_point(point=(point["pos"]["x"], point["pos"]["y"])) for point in (axis["_start"], axis["_end"])]
    delta = tuple(end - start for start, end in zip(*points, strict=True))
    length = hypot(*delta)
    if not isfinite(length) or length < 1e-8:
        raise ConstructionError("native revolve axis endpoints must span at least 1e-8 metres")
    direction = tuple(value / length for value in delta)
    fields = component_reference_fields(component=component)
    fields.update({
        "ff0": {"f00": profile.profile["f08"], "f08": logged_creation_time(timestamps=(profile_created_at,))},
        "f0f8": line_handle(sketch=sketch, line=axis, lines=sketch["_line_nodes"]),
    })
    selected = Obj("moCompSketchEntHandle_c", DerivedFields(fields=fields, derived={"f100": lambda: axis["f08"]}))
    return Obj("moLineRef_w", {
        **reference_wrapper_fields(reference=selected),
        "fc8": _point(points[0]), "fe0": _point(direction), "ff8": 0,
        "fb0": 0.0, "fb8": sum(value * unit for value, unit in zip(delta, direction, strict=True)),
    })


def live_revolution(*, feature: Obj, source: RevolveProfile, allocator, component: Obj, profile_created_at: int, angle_rad: float, reverse_direction: bool, design_intent: bool, selected_leader: int) -> RevolutionGraph:
    if not isinstance(feature, Obj) or feature.cls != "moRevolution_c" or type(feature.get("f08")) is not int or feature["f08"] < 0:
        raise ConstructionError("revolve requires an allocated native body feature")
    if not isinstance(source, RevolveProfile) or not isinstance(component, Obj) or component.cls != "moUnitComponent_c":
        raise ConstructionError("revolve requires a constructed local profile and unit component")
    owner = feature.get("owner")
    if not isinstance(owner, Obj) or owner.cls != "moPart_c" or component.get("owner") is not owner or source.profile.profile.get("owner") is not owner:
        raise ConstructionError("revolve feature, profile and component must share their model owner")
    for field in ("f368", "f388", "f780"):
        if field not in feature.f:
            raise ConstructionError(f"revolve owner is missing the body-feature base field {field}")
    if feature.get("f8d8") is not None or feature.get("f60") != node_list():
        raise ConstructionError("revolve requires a fresh feature with an empty dependency list")
    axis = source.axis
    if axis not in source.profile.lines or not axis["f54"] & 8 or axis.get("_sketch") is not source.profile.sketch:
        raise ConstructionError("revolve axis must be an actual construction line in the selected sketch")
    if type(reverse_direction) is not bool:
        raise ConstructionError("revolve direction must be boolean")
    if isinstance(angle_rad, bool) or not isinstance(angle_rad, (int, float)) or not isfinite(angle_rad) or not 1e-8 < angle_rad <= tau:
        raise ConstructionError("ordinary revolve requires a finite positive angle through one full turn")
    reference = _axis_reference(source=source, component=component, profile_created_at=profile_created_at)
    angle = _construct_feature_dimension(feature=feature, dimension_id=1, value=angle_rad, angular=True, allocator=allocator, design_intent=design_intent, selected_leader=selected_leader)
    angle.display["f5b0"]["data"] = pack("<d", angle.parameter["f58"])
    end = Obj("moRevEndSpec_c", {
        "f08": 1, "f138": 0, "f13c": 0, "f0c": 0, "f10": 0,
        "f118": None, "f120": None, "f128": None, "f130": None,
        "f38": 0.01, "f40": 0.01, "f140": 0, "f144": 0,
        "f18": angle.display, "f20": None, "f28": None, "f30": None,
        "_owner": feature,
    })
    feature.f.update({
        "f60": node_list((source.profile.profile,)), "f808": None, "f824": int(reverse_direction),
        "f810": None, "f820": 0, "f818": Obj("suObList", empty_object_list()),
        "f828": 3, "f870": 1, "f830": reference, "f8d8": end, "f8e8": 0,
    })
    return RevolutionGraph(feature=feature, axis_reference=reference, end=end, angle=angle)
