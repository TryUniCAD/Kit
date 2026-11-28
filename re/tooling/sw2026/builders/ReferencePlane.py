from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from Core import Obj
from builders.Extrude import DimensionGraph, _construct_feature_dimension
from builders.Metadata import boolean, fields, integer
from builders.Model import PersistentIds, atom_feature, component_plane, reference_wrapper_fields
from builders.Sketch import ConstructionError, PlaneFrame, frame_transform


@dataclass(frozen=True, kw_only=True)
class OffsetPlaneGraph:
    feature: Obj
    support: Obj
    frame: PlaneFrame
    distance: DimensionGraph
    reverse: bool


def _point(value):
    return dict(zip("xyz", value, strict=True))


def _principal_support(support, owner):
    if not isinstance(owner, Obj) or owner.cls != "moPart_c":
        raise ConstructionError("an ordinary offset plane requires its generated part")
    if not isinstance(support, Obj) or support.cls != "moRefPlane_c" or support.get("owner") is not owner:
        raise ConstructionError("an offset plane must select a datum in its actual part")
    if support.get("_principal_axis") not in ("x", "y", "z") or support["f6f8"].cls != "moDefaultRefPlnData_c":
        raise ConstructionError("offset discovery supports only a generated principal datum")
    data = support["f6f8"]
    return PlaneFrame(origin=tuple(data["root"][axis] for axis in "xyz"),
                      u=support["_plane_u"], v=support["_plane_v"])


def _selected_wrapper(*, support, owner, frame, created_at):
    selected = component_plane(plane=support, component=owner["f990"], created_at=created_at,
                               principal_normal=frame.normal)
    values = reference_wrapper_fields(reference=selected)
    values.update({
        "f68": 1,
        "fd0": _point(frame.origin), "fe8": _point(frame.normal),
        "f100": frame_transform(frame=frame), "f188": _point((0.0, 0.0, 0.0)),
        **{key: support["f6f8"][f"b{index}"] for index, key in enumerate(("fb0", "fb8", "fc0", "fc8"))},
    })
    return values


def construct_offset_plane(*, request, support, owner, allocator, date_code, parasolid_version,
                           created_at, design_intent, selected_leader):
    request = fields(request, "ordinary offset-plane discovery", ("name", "distance_m", "reverse"))
    reverse = boolean(request["reverse"], "offset direction reversal")
    value = request["distance_m"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 1e-14:
        raise ConstructionError("offset distance must be finite and at least 1e-14 metres")
    if not isinstance(allocator, PersistentIds):
        raise ConstructionError("an offset plane requires the part's persistent ID allocator")
    boolean(design_intent, "offset dimension design intent")
    integer(selected_leader, "selected offset dimension leader", low=-(1 << 31), high=(1 << 31) - 1)
    base = _principal_support(support, owner)
    origin = tuple(a + (-value if reverse else value) * n for a, n in zip(base.origin, base.normal, strict=True))
    frame = PlaneFrame(origin=origin, u=base.u, v=base.v)
    plane = atom_feature(cls="moRefPlane_c", name=request["name"], owner=owner, allocator=None,
                         date_code=date_code, parasolid_version=parasolid_version)
    distance = _construct_feature_dimension(feature=plane, dimension_id=1, value=value, angular=False,
                                            allocator=allocator, design_intent=design_intent,
                                            selected_leader=selected_leader)
    data = Obj("moFaceRefPlnData_c", {
        "root": _point(frame.origin), "normal": _point(frame.normal), "f20": frame_transform(frame=frame),
        **dict.fromkeys(("b0", "b1", "b2", "b3"), 0.0),
        "f48": None, "f50": 0, "f54": -4, "f58": -4, "old_e5": 0,
        "f5c": 5, "f60": 0, "f64": 0, "f68": None, "f70": None, "f78": None,
        "f90": _selected_wrapper(support=support, owner=owner, frame=base, created_at=created_at),
        "f98": distance.display, "fa0": int(reverse), "fa4": 1, "has_fa8": 0, "fb4": 0,
    })
    plane.f.update({
        "f6c0": _point((0.0, 0.0, 0.0)), "f6dc": 4, "f6e0": 0, "f6e8": None, "f6f0": 0,
        "f6f8": data, "_plane_u": frame.u, "_plane_v": frame.v,
    })
    allocator.allocate(plane)
    return OffsetPlaneGraph(feature=plane, support=support, frame=frame, distance=distance, reverse=reverse)
