from __future__ import annotations

from Core import Obj
from builders.Definition import identity_transform
from builders.DrawingFrontProjection import FrontProjection
from builders.DrawingSheetObjects import _detail_folder, _sheet_plane, _sheet_plane_reference, _sheet_profile
from builders.Metadata import fields
from builders.Model import PersistentIds, node_list


def _view_sketch(*, owner, component, allocator, created_at, plane_name, profile_name, origin, transform, sheet_plane, target):
    plane = _sheet_plane(owner=owner, name=plane_name, transform=transform, provenance=target)
    data = plane["f6f8"]
    data["root"] = dict(origin)
    if sheet_plane:
        plane["f6f8"] = Obj("moDrawingRefPlnData_c", {
            **data.f, "b0": 0.0, "b1": 0.0, "b2": 0.0, "b3": 0.0, "f88": identity_transform(),
        })
    else:
        plane["f6c0"] = {"x": origin["x"] + data["b1"], "y": origin["y"] + data["b2"], "z": origin["z"]}
    reference = _sheet_plane_reference(plane=plane, component=component)
    allocator.allocate(plane)
    profile = _sheet_profile(owner=owner, name=profile_name, reference=reference, allocator=allocator,
                             transform=transform, created_at=created_at, provenance=target)
    for node in (plane, profile):
        node["f0c"] &= 0xFFFD7FF8
    return plane, profile


def front_view_supports(*, view, drawing, projection, names, allocator, created_at, target):
    if not isinstance(view, Obj) or view.cls != "moAbsoluteView" or view.get("f08") != -1:
        raise ValueError("front-view supports require a view before persistent allocation")
    if not isinstance(drawing, Obj) or drawing.cls != "moDrawing_c" or not isinstance(projection, FrontProjection):
        raise ValueError("front-view supports require their actual drawing and projection")
    if not isinstance(allocator, PersistentIds):
        raise ValueError("front-view supports require the drawing allocator")
    names = fields(names, "view support names", ("detail", "sheet_plane", "sheet_profile", "model_plane", "model_profile"))
    detail = _detail_folder(owner=view, name=names["detail"], allocator=allocator, provenance=target)
    detail["f0c"] &= 0xFFFD7FF8
    allocator.allocate(view)
    common = {"owner": view, "component": drawing["f990"], "allocator": allocator, "created_at": created_at, "target": target}
    sheet_plane, sheet_profile = _view_sketch(
        plane_name=names["sheet_plane"], profile_name=names["sheet_profile"], origin=projection.view["f778"],
        transform=projection.sheet_sketch_transform, sheet_plane=True, **common,
    )
    model_plane, model_profile = _view_sketch(
        plane_name=names["model_plane"], profile_name=names["model_profile"], origin=projection.view["f648"],
        transform=projection.model_plane_transform, sheet_plane=False, **common,
    )
    view.f.update({
        "f60": node_list((detail, sheet_plane, sheet_profile, model_plane, model_profile)),
        "f630": detail, "has_f7c8": 1, "f7c8": sheet_profile, "has_fde0": 1, "fde0": model_profile,
    })
