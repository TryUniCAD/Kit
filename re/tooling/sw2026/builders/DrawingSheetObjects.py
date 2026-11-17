from __future__ import annotations

from Core import Obj
from builders.Definition import identity_transform
from builders.DrawingSheet import DrawingSheet
from builders.DrawingTail import drawing_feature_filetime
from builders.Model import absolute_reference_plane, feature, model_feature, node_list, object_list, unregistered_plane_reference
from builders.Sketch import PlaneFrame, _bind_local_ref_flag, new_profile


_SHEET_FRAME = PlaneFrame(origin=(0.0, 0.0, 0.0), u=(1.0, 0.0, 0.0), v=(0.0, 1.0, 0.0))
_DEFAULT_PLANE_WIDTH = 0.1618
_DEFAULT_PLANE_HEIGHT = 0.1
_DETAIL_LIST_OFFSETS = (
    0x358, 0x3A0, 0x3E8, 0x430, 0x478, 0x4C0, 0x508, 0x550, 0x598, 0x5E0,
    0x628, 0x670, 0x700, 0x748, 0x790, 0x7D8, 0x820, 0x868, 0x8B0, 0x8F8,
    0x940, 0x988, 0x9D0, 0xA18, 0xAA8, 0xAF0, 0xB38, 0xB80, 0xBC8, 0xC10,
    0xC58, 0xCA0, 0xCE8, 0xD30,
)


def _sheet_plane(*, owner, name, transform, provenance):
    if name is None:
        raise ValueError("sheet support plane requires an authored name")
    root = dict(zip("xyz", _SHEET_FRAME.origin, strict=True))
    normal = dict(zip("xyz", _SHEET_FRAME.normal, strict=True))
    half_width = _DEFAULT_PLANE_WIDTH * 0.5
    half_height = _DEFAULT_PLANE_HEIGHT * 0.5
    return absolute_reference_plane(owner=owner, name=name, root=root, normal=normal, transform=transform,
                                    bounds=(half_width, -half_width, half_height, -half_height), **provenance)


def _sheet_profile(*, owner, name, reference, allocator, transform, created_at, provenance):
    profile = model_feature(cls="moProfileFeature_c", name=name, owner=owner, allocator=allocator, **provenance)
    graph = new_profile(profile=profile, plane=reference, frame=_SHEET_FRAME)
    graph.sketch["f128"] = 0
    _bind_local_ref_flag(sketch=graph.sketch)
    profile.f.update({**drawing_feature_filetime(created_at), "pd_ff0": transform})
    return profile


def _detail_folder(*, owner, name, allocator, provenance):
    folder = feature(cls="moDetailFolder_c", name=name, owner=owner, allocator=allocator, **provenance)
    folder.f.update({f"f{offset:x}": object_list() for offset in _DETAIL_LIST_OFFSETS})
    folder.f.update({"fd90": identity_transform(), "fd78": None, "has_fd98": 0, "fde8": 0})
    return folder


def empty_drawing_sheet(*, settings, owner, allocator, plane_name, profile_name, detail_name, created_at, date_code, parasolid_version):
    if not isinstance(settings, DrawingSheet) or not isinstance(owner, Obj) or owner.cls != "moDrawing_c":
        raise ValueError("empty sheet support requires authored drawing settings and the actual drawing owner")
    component = owner.get("f990")
    if not isinstance(component, Obj) or component.cls != "moUnitComponent_c" or component.get("owner") is not owner:
        raise ValueError("empty sheet support requires the owning drawing's unit component")
    provenance = {"date_code": date_code, "parasolid_version": parasolid_version}
    sheet = model_feature(cls="moDrSheet", name=settings.name, owner=owner, allocator=allocator, **provenance)
    plane = _sheet_plane(owner=sheet, name=plane_name, transform=settings.model_sketch_frame(), provenance=provenance)
    reference = unregistered_plane_reference(plane=plane, component=component)
    allocator.allocate(plane)
    profile = _sheet_profile(owner=sheet, name=profile_name, reference=reference, allocator=allocator,
                             transform=settings.model_sketch_frame(), created_at=created_at, provenance=provenance)
    folder = _detail_folder(owner=sheet, name=detail_name, allocator=allocator, provenance=provenance)
    for node in (sheet, plane, profile, folder):
        node["f0c"] &= 0xFFFD7FF8
    sheet.f.update({
        **settings.authored_fields(),
        "f60": node_list((plane, profile, folder)),
        "has_f408": 1, "f408": profile, "has_f468": 0, "has_f418": 0,
        "f3b0": 0, "f420": 0, "f428": 0, "f3c8": None,
        "f438": Obj("suObList", object_list()), "has_f430": 0,
        "f390": folder, "f448": 1, "has_f450": 0,
        "f3d8": 1, "f368_marker": 0xFFFF, "f474": 0,
        "f4d0": 0, "f4d4": 0, "f4e0": 1, "f4f0": 0,
        "n_ink_views": 0, "ink_views": [],
    })
    return sheet


def sheet_ui_sketch(*, settings, sheet):
    if not isinstance(settings, DrawingSheet) or not isinstance(sheet, Obj) or sheet.cls != "moDrSheet":
        raise ValueError("UI sketch construction requires the generated sheet and its settings")
    if sheet.get("f3f8") != settings.scale_numerator or sheet.get("f400") != settings.scale_denominator:
        raise ValueError("UI sketch scale must agree with the generated sheet")
    return Obj("uoSketch", {"profile_feature_id": sheet["f408"]["f08"], "f80": settings.ui_sketch_frame()})
