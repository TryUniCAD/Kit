from __future__ import annotations

from Core import Obj
from builders.Definition import identity_transform
from builders.DrawingFrontProjection import front_projection
from builders.DrawingSheet import DrawingSheet
from builders.DrawingTail import drawing_feature_filetime
from builders.DrawingViewLinks import single_view_links
from builders.DrawingViewSupports import front_view_supports
from builders.Metadata import fields, text
from builders.Model import PersistentIds, model_feature, node_list, object_list
from builders.Part import PartConstruction


def _view_state(*, drawing, child):
    detail = drawing["fae0"]
    state = {name: 0 for name in (
        "f798", "f79c", "has_f6c8", "has_f8e0", "f7bc", "f7a8", "f7c0", "f7b4", "f8ec", "has_f9d8", "na10",
        "has_fb50", "n860", "na18", "fb74", "f8e8", "fd94", "fdb8", "has_fe78", "fe8c", "nf50", "nf68",
        "f540", "ffa4", "ffb4", "f558", "has_view_bodies", "ffbc", "f590", "f1010", "f1020", "f1028", "f102c",
    )}
    state.update({name: 0.0 for name in ("f9e8", "f9f0", "f9f8", "fa00", "fb68")})
    state.update({name: None for name in ("f968", "f8f8", "f640", "f658", "fb58", "f1008")})
    state.update({name: "" for name in ("fe30_name", "f548", "f550", "fff8")})
    state.update({name: [] for name in ("f858", "ff48", "ff60")})
    state.update({name: object_list() for name in (
        "fd28", "f900", "fb78", "fa20", "fa68", "fab0", "faf8", "fc28", "fc70", "fcb8", "fd48", "ff70",
    )})
    state.update({
        "f6b8": identity_transform(), "f6c0": identity_transform(),
        "f608": {f"b{index}": value for index, value in enumerate((0.0, 0.0, 0.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, -2.0))},
        "fe30_flags": -1, "f7ac": 2, "f7b0": 2, "f8f0": -1, "f6b0": -1.0,
        "fe40": 3, "f410": -1, "f3e8": 0.01, "f3f0": 0.003175, "fe94": child.model["ff3c"],
        "ffa8": detail["f15c"], "ffac": detail["f160"], "f7a0": detail["f2c6c"],
        "f55c": -1, "f594": -1, "f3f8": 1.0, "f5a8": 1, "f1030": 1,
        "f610": (1 << 11) | (1 << 7) | (1 << 4) | (1 << 3),
        "f614": sum(1 << bit for bit in (2, 8, 10, 16, 20, 21, 22)),
        "f618": (1 << 15) if detail["f20"] & (1 << 18) else 0,
        "f61c": (1 << 3) | (1 << 2) | 1,
    })
    return state


def add_front_view(*, drawing, child, sheet_settings, requested, created_at, target):
    if not isinstance(drawing, Obj) or drawing.cls != "moDrawing_c":
        raise ValueError("front-view construction requires the actual drawing model")
    if not isinstance(child, PartConstruction) or child.blind_pocket is not None:
        raise ValueError("front-view construction admits a single generated boss without further features")
    requested = fields(requested, "ordinary front view", ("name", "orientation", "position", "scale", "supports"))
    names = fields(requested["supports"], "view support names", ("detail", "sheet_plane", "sheet_profile", "model_plane", "model_profile"))
    if any(not text(name, "view node name") for name in (requested["name"], *names.values())):
        raise ValueError("front views require nonempty names for the view and its supports")
    sheet = drawing["f1430"]
    if not isinstance(sheet_settings, DrawingSheet) or sheet["f18"]["f08"] != sheet_settings.name or any(
        sheet[field] != value for field, value in sheet_settings.authored_fields().items()
    ):
        raise ValueError("front-view projection settings must describe the actual sheet")
    children = [row["o"] for row in sheet["f60"]["list"]["items"]]
    if tuple(node.cls for node in children) != ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c") or drawing["n1578"] or drawing["n1740"]:
        raise ValueError("ordinary front-view construction starts from the generated unformatted sheet")
    projection = front_projection(child=child, sheet=sheet_settings, orientation=requested["orientation"],
                                  position=requested["position"], scale=requested["scale"])
    view = model_feature(cls="moAbsoluteView", name=requested["name"], owner=sheet, allocator=None, **target)
    view.f.update(_view_state(drawing=drawing, child=child))
    view.f.update({**projection.view, **drawing_feature_filetime(created_at), "f0c": 0})
    allocator = PersistentIds(next_id=drawing["fa8"]["f08"])
    refs = single_view_links(drawing=drawing, child=child, local_bounds=projection.view["f600"],
                             allocator=allocator, created_at=created_at, target=target)
    view["f5d8"] = refs.internal
    front_view_supports(view=view, drawing=drawing, projection=projection, names=names,
                        allocator=allocator, created_at=created_at, target=target)
    sheet["f60"] = node_list((*children, view))
    drawing["fa8"].f.update(f08=allocator.next_id, bboxflag=1, bbox=projection.header_bounds)
    return view
