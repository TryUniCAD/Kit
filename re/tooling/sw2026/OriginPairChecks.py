from __future__ import annotations

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadAllProfiles import ReadAllProfiles


def require(value, message):
    if not value:
        raise ValueError(message)


def display_row(named):
    values = tuple(item for group in ReadAllProfiles(named.DocumentValue, 19000) for item in group.ItemsValue)
    require(len(values) == 1, "origin pair requires exactly one retained display")
    return values[0]


def check_display(named, child, header):
    item = display_row(named)
    fields, wrapper = item.DisplayValue.FieldsValue, item.ReferenceValue.FieldsValue
    origin = next(node for node in child if node.ClassValue == RuntimeClass("moOriginProfileFeature_c", 1))
    feature_id = FieldInt(origin.FieldsValue, "f08")
    stamp = DatumTime(header, feature_id)
    require(wrapper["ff0"] == {"f00": feature_id, "f08": stamp}, "origin pair used a foreign feature identity or creation epoch")
    chain = ArchiveNode.RequireNode(wrapper["f58"])
    reference_chain = ArchiveNode.RequireNode(chain.FieldsValue["f20"])
    entries = ArchiveNode.RequireNode(reference_chain.FieldsValue["f08"])
    require(entries.ClassValue == RuntimeClass("moExtFeatureList_c", 1) and entries.FieldsValue["n"] == len(entries.FieldsValue["f08"]) == 1,
            "origin pair lost its actual one entry component path")
    external = ArchiveNode.RequireNode(entries.FieldsValue["f08"][0]["o"])
    reference = ArchiveNode.RequireNode(item.ViewValue.FieldsValue["f5d8"])
    model = ArchiveNode.RequireNode(named.DocumentValue.FieldsValue["model"])
    require(chain.ClassValue == RuntimeClass("moChainComponent_c", 1) and chain.FieldsValue["owner"] is model
            and reference.ClassValue == RuntimeClass("moReferenceInternal_c", 1) and external is reference.FieldsValue["f4f8"]
            and external.FieldsValue["f50"] is reference, "origin pair lost actual external reference or model aliases")
    require(reference_chain.FieldsValue["f20"] == reference_chain.FieldsValue["f24"] == 0
            and chain.FieldsValue["f30"] == (101 + FieldInt(reference.FieldsValue, "f3f0")) & 0xffffffff,
            "origin pair path construction changed its native bookkeeping")
    require(fields["f30"] is item.FolderValue and fields["f40"] is item.ViewValue and fields["f48"] is item.ReferenceValue,
            "origin pair lost display owner aliases")
    require(fields["f68"] is not fields["fb0"] and not fields["f68"]["items"] and not fields["fb0"]["items"]
            and fields["f58"] == 10 and model.FieldsValue["fd44"] == 11,
            "origin pair did not allocate exactly one display from the actual model counter")
    require(fields["n1e0"] == 0 and not fields["f1e0"] and fields["f200"] == 1 and fields["ff8"] is None
            and fields["linked"] == 0 and item.CanHideSuppressed, "origin pair introduced unsupported linked or bitmap state")
    require(fields["f08"] == {"f00": 65535, "f02": 0, "f04": 3,
                                      "f08": {"f00": 0xffffffff, "f04": 0, "f08": {"f06": 0, "f00": -1.0}}}
            and (fields["f50"], fields["f54"], fields["f11c"], fields["f118"]) == (0, 0, 0, 19000),
            "origin display did not preserve its independently proved native constructor presentation")
    ordinary = tuple(node for node in child if node.ClassValue == RuntimeClass("moProfileFeature_c", 1))
    require(len(ordinary) == 1 and ordinary[0].FieldsValue["f08"] != feature_id, "origin pair selected the ordinary child sketch")
    return {"child_origin_id": feature_id, "creation_epoch": stamp, "ordinary_profile_id": ordinary[0].FieldsValue["f08"],
            "display_id": fields["f58"], "model_next_display_id": model.FieldsValue["fd44"],
            "component_stamp": chain.FieldsValue["f30"], "component_acquisition_count": reference_chain.FieldsValue["f20"],
            "actual_origin_and_component_aliases": True, "actual_folder_and_view_aliases": True,
            "bitmaps_empty": True, "native_lifecycle_acceptance": False}
