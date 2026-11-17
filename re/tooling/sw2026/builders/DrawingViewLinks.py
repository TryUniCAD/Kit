from __future__ import annotations

from dataclasses import dataclass

from Core import Obj
from builders.Assembly import ordinary_part_reference_stamps
from builders.AssemblyDocument import _child_directory_entry
from builders.AssemblyOccurrences import _configuration_pair, _external_feature, _shared_file
from builders.Definition import identity_transform
from builders.DrawingTail import drawing_feature_filetime
from builders.Model import PersistentIds, feature, object_list
from builders.Part import PartConstruction


@dataclass(frozen=True, slots=True)
class DrawingViewLinks:
    directory: Obj
    internal: Obj
    properties: Obj


def _drawing_reference(*, child, entry, drawing, kind, name, allocator, target):
    reference = feature(cls=kind, name=name, owner=drawing, allocator=allocator, **target)
    reference.f.update(ordinary_part_reference_stamps(child_model=child.model, child_header=child.model_header, assigned_transform=True))
    reference.f.update({key: 0 for key in (
        "has_discarded_xform", "has_f378", "has_f370", "f388", "f408", "f418", "f41c", "f450", "f454", "f458",
        "f49c", "f4a0", "f4c0", "f4d8", "f4dc", "f4f0", "f524", "f530", "f550", "f368",
    )})
    reference.f.update({key: None for key in ("f468", "f470", "f488", "f490", "f4f8", "f538", "f548", "discarded_stack")})
    reference.f.update({
        "has_f360": 1, "f360": identity_transform(), "f3b0": entry,
        "f3c0": _configuration_pair(child.configuration, owner=child.model, kind="moPartConfiguration_c"),
        "f3dc": -1, "f400": 3, "f4a4": -1, "f4b0": -1, "f4b4": -1, "f500": "", "f508": "", "f55c": 101,
    })
    return reference


def single_view_links(*, drawing, child, local_bounds, allocator, created_at, target):
    if not isinstance(drawing, Obj) or drawing.cls != "moDrawing_c" or not isinstance(child, PartConstruction):
        raise ValueError("front-view linking requires the generated drawing and part")
    if not isinstance(allocator, PersistentIds) or drawing["f16a8"]["n10"] or drawing["fa8"]["f30"] is not None:
        raise ValueError("the ordinary view link starts with an empty drawing reference directory")
    owner_file = _shared_file(drawing["fa8"]["f38"], kind=4)
    entry = _child_directory_entry(child=child, uses=1)
    child_name = entry["shared"]["h10"]["f08"]
    common = {"child": child, "entry": entry, "drawing": drawing, "target": target}
    internal = _drawing_reference(kind="moReferenceInternal_c", name=f"{child_name}-1", allocator=allocator, **common)
    internal.f.update({"f0c": 0, "has_f370": 1, "f370": dict(local_bounds), **drawing_feature_filetime(created_at)})
    internal["f4f8"] = _external_feature(reference=internal, owner_file=owner_file, backlink=True)
    property_model = _drawing_reference(kind="moReferenceModel_c", name=child_name, allocator=None, **common)
    property_model.f.update({"f18": None, "f1f8": child_name})
    properties = drawing["f16a8"]
    properties.f.update(n10=1, f08=[{"model": property_model, "properties": Obj("suObArray", object_list())}])
    drawing["fa8"]["f30"] = Obj("moExtObjectList_c", object_list((entry,)))
    return DrawingViewLinks(entry, internal, properties)
