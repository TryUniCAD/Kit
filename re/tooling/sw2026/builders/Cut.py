from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from builders.Circle import circle_profile
from builders.Extrude import DimensionGraph, ExtrusionGraph, live_blind_cut
from builders.Metadata import fields
from builders.Model import body_feature, component_plane, model_feature
from builders.Radial import circle_dimension
from builders.Sketch import ConstructionError, _vector


@dataclass(frozen=True, kw_only=True)
class BlindPocketGraph:
    extrusion: ExtrusionGraph
    radial: DimensionGraph
    scope: str


def _rectangular_bounds(boss):
    profile = boss.profile
    if profile.point_count != 4 or profile.line_count != 4 or profile.arc_count != 0:
        raise ConstructionError("blind cut discovery requires a single rectangular boss")
    points = [(point["pos"]["x"], point["pos"]["y"]) for point in profile.sketch["_point_nodes"]]
    xs, ys = zip(*points, strict=True)
    left, right, bottom, top = min(xs), max(xs), min(ys), max(ys)
    if set(points) != {(x, y) for x in (left, right) for y in (bottom, top)}:
        raise ConstructionError("blind cut discovery requires an axis aligned rectangular boss")
    if not all(isfinite(length) and length > 0.0 for length in (right - left, top - bottom)):
        raise ConstructionError("blind cut boss requires finite positive side lengths")
    return left, right, bottom, top


def _validate_geometry(*, request, boss):
    left, right, bottom, top = _rectangular_bounds(boss)
    x, y = center = _vector(value=request["center_m"], size=2)
    radius, depth = request["radius_m"], request["depth_m"]
    if type(radius) not in (int, float) or not isfinite(radius) or not 0 < radius < min(x - left, right - x, y - bottom, top - y):
        raise ConstructionError("pocket circle must lie strictly inside the boss profile")
    if center == (left + (right - left) / 2, bottom + (top - bottom) / 2):
        raise ConstructionError("discovery requires an eccentric pocket")
    if type(depth) not in (int, float) or not isfinite(depth) or not 1e-14 <= depth < boss.depth:
        raise ConstructionError("pocket depth must be a positive blind depth smaller than the boss depth")
    return center


def blind_pocket(*, request, boss, feature_values, reference_values, features, design_intent, selected_leader):
    request = fields(request, "blind cut discovery", (
        "sketch_name", "feature_name", "center_m", "radius_m", "depth_m", "dimension_text_point_m", "scope",
    ))
    scope = request["scope"]
    if scope not in ("all_bodies", "empty_feature_scope"):
        raise ConstructionError("blind cut discovery requires all_bodies or empty_feature_scope")
    names = (request["sketch_name"], request["feature_name"])
    if any(not isinstance(name, str) or not name.strip() or "@" in name for name in names):
        raise ConstructionError("pocket sketch and feature require nonempty names without dimension separators")
    used_names = {node["f18"]["f08"].casefold() for node in features}
    if len(used_names | {name.casefold() for name in names}) != len(used_names) + len(names):
        raise ConstructionError("pocket sketch and feature names must be distinct in the part")
    center = _validate_geometry(request=request, boss=boss)
    sketch_node = model_feature(cls="moProfileFeature_c", name=request["sketch_name"], **feature_values)
    profile = circle_profile(
        center_m=center, radius_m=request["radius_m"], profile=sketch_node,
        plane=component_plane(**reference_values), frame=boss.profile.profile["_frame"],
    )
    dimension_options = {
        "allocator": feature_values["allocator"], "design_intent": design_intent,
        "selected_leader": selected_leader,
    }
    radial = circle_dimension(
        graph=profile, mode="radius", text_point_m=request["dimension_text_point_m"], fix_center=True,
        **dimension_options,
    )
    cut_node = body_feature(cls="moICE_c", name=request["feature_name"], **feature_values)
    cut = live_blind_cut(feature=cut_node, profile=profile, depth=request["depth_m"], **dimension_options)
    if any(cut_node[name] != 0 for name in ("has_f528", "has_f530", "has_f548", "n494", "has_f4a8", "has_f4b0", "has_f4c0", "has_f4c8")) or cut_node["f538"] is not None or "f558" in cut_node.f:
        raise ConstructionError("blind cut discovery requires the constructor's absent body and chooser state")
    cut_node["f544"] = int(scope == "empty_feature_scope")
    return BlindPocketGraph(extrusion=cut, radial=radial, scope=scope)
