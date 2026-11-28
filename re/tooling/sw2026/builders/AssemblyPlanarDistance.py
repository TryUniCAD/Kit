from __future__ import annotations

from math import isclose, isfinite

from Core import Obj
from builders.Extrude import DimensionGraph, _construct_feature_dimension
from builders.Metadata import boolean, fields, integer, sequence
from builders.Model import PersistentIds
from builders.Sketch import ConstructionError, _dot
from builders.Styles import number


def _assembly_owner(mate: Obj) -> Obj:
    owner = mate.get("owner")
    if isinstance(owner, Obj) and owner.cls == "moMateGroup_c":
        owner = owner.get("owner")
    if not isinstance(owner, Obj) or owner.cls != "moAssembly_c":
        raise ConstructionError("a planar distance mate requires its filed assembly")
    return owner


def _coordinate_triple(value, label) -> tuple[float, float, float]:
    coordinates = fields(value, label, ("x", "y", "z"))
    x, y, z = (number(coordinates[axis], label) for axis in "xyz")
    return x, y, z


def _principal_plane(wrapper: Obj, assembly: Obj):
    if not isinstance(wrapper, Obj) or wrapper.cls != "moPlaneRef_w" or wrapper.get("f60") is not None:
        raise ConstructionError("a planar distance mate requires ordinary resolved plane wrappers")
    reference = wrapper.get("f58")
    if not isinstance(reference, Obj) or reference.cls != "moCompRefPlane_c":
        raise ConstructionError("a planar distance mate requires principal datum references")
    kind = reference.get("f100")
    if type(kind) is not int or kind not in (1, 2, 3):
        raise ConstructionError("a planar distance mate requires principal datum references")
    chain = reference.get("f58")
    if not isinstance(chain, Obj) or chain.cls != "moChainComponent_c" or chain.get("owner") is not assembly:
        raise ConstructionError("both distance endpoints must be resolved in the filed assembly")
    return _coordinate_triple(wrapper.get("fd0"), "plane origin"), _coordinate_triple(wrapper.get("fe8"), "plane normal")


def _require_positive_planes(mate: Obj, assembly: Obj) -> None:
    entries = sequence(mate.get("f410"), "planar distance endpoints")
    if len(entries) != 2:
        raise ConstructionError("a planar distance mate requires two endpoints")
    first, second = (fields(entry, "distance endpoint", ("o",))["o"] for entry in entries)
    origin, normal = _principal_plane(first, assembly)
    other_origin, other_normal = _principal_plane(second, assembly)
    same_direction = isclose(_dot(left=normal, right=other_normal), 1.0, rel_tol=0.0, abs_tol=1e-10)
    unit_normals = all(isclose(_dot(left=axis, right=axis), 1.0, rel_tol=0.0, abs_tol=1e-10) for axis in (normal, other_normal))
    difference = tuple(b - a for a, b in zip(origin, other_origin, strict=True))
    separation = _dot(left=difference, right=normal)
    if not same_direction or not unit_normals or not isfinite(separation) or separation <= 0.0:
        raise ConstructionError("the ordered principal planes must be aligned with positive signed separation")


def _linear_style(assembly: Obj) -> tuple[dict, int, int]:
    detail = assembly["fae0"]["f13b0"]
    style = detail["fe0"]
    if style["f44"] != 0 or detail["fd8"] & 2:
        raise ConstructionError("planar distance construction requires zero tolerance and freely placed text")
    unit_mode = integer(detail["f6c"], "linear display unit mode", high=0xFFFF)
    projection = {
        "f870": unit_mode,
        "f874": unit_mode,
        "fb68": integer(style["fc"], "linear display primary precision", high=0xFFFF),
        "fb6c": integer(style["f10"], "linear display secondary precision", high=0xFFFF),
        "f8ec": integer(style["f84"], "linear display precision mode", high=0xFFFF),
        "ff00": integer(detail["fc0"], "linear display ff00", low=-(1 << 31), high=(1 << 31) - 1),
        "ff10": int(bool(style["fe0"] & 0x10000)),
        "fe40": integer(style["f08"], "linear display fe40"),
        "f30c": dict(style["fd0"]["f10"]),
        "f320": dict(style["fd8"]["f10"]),
    }
    under_text = 0x40 if detail["f74"] == 0 and detail["f60"] == 0 else 0
    flags = detail["fd8"] & 0x100000
    flags |= 0x1000 if style["f78"] else 0
    flags |= 0x2000 if style["f9c"] else 0
    return projection, under_text, flags


def construct_planar_distance(
    *,
    mate: Obj,
    distance_m: float,
    allocator: PersistentIds,
    design_intent: bool,
    selected_leader: int,
) -> DimensionGraph:
    if not isinstance(mate, Obj) or mate.cls != "moMateDistanceDim_c":
        raise ConstructionError("a planar distance dimension requires its concrete distance mate")
    if type(mate.get("f08")) is not int or mate["f08"] != -1 or mate.get("f4b8") is not None:
        raise ConstructionError("allocate the driving dimension before registering the mate")
    if type(mate.get("f3b4")) is not int or mate["f3b4"] != 1:
        raise ConstructionError("planar distance construction requires explicit aligned mate input")
    if not isinstance(allocator, PersistentIds):
        raise ConstructionError("planar distance construction requires the assembly's persistent ID allocator")
    assembly = _assembly_owner(mate)
    distance = number(distance_m, "driving distance in metres", low=1e-14)
    boolean(design_intent, "dimension design intent")
    integer(selected_leader, "selected dimension leader", low=-(1 << 31), high=(1 << 31) - 1)
    _require_positive_planes(mate, assembly)
    style, under_text, style_flags = _linear_style(assembly)
    graph = _construct_feature_dimension(
        feature=mate,
        dimension_id=1,
        value=distance,
        angular=False,
        allocator=allocator,
        design_intent=design_intent,
        selected_leader=selected_leader,
    )
    display = graph.display
    display.f.update(style)
    display["f6a0"]["f10"] = 18
    display["f8a4"] = (display["f8a4"] & ~0x50) | under_text
    display["fb64"] = (display["fb64"] & ~0x103000) | style_flags
    mate.f.update(f4b8=display, f4c0=1, f4d8=1, f4dc=3, f4e0=3, f4f4=0)
    return graph
