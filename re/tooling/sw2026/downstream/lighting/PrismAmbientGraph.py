from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from downstream.lighting.AmbientInput import AmbientInput
from downstream.lighting.AttachAmbientMut import AttachAmbientMut
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def add_authored_ambient(archive, specification, model_second, enabled):
    link = ReadNativeLink(archive, 0)
    root = link.ConfigValue.RootValue
    header = link.ConfigValue.HeaderValue
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    current = manager.RootValue.FieldsValue["f360"]
    before_flags = (root.FieldsValue["f0c"], root.FieldsValue["f1e0"].FieldsValue["f0c"])
    before_ids = tuple((value.ClassValue.NameValue, value.FieldsValue["f08"])
                       for value in link.ResolvedValue.RootsValue)
    before_next = header.FieldsValue["f08"]
    if type(before_next) is not int or before_next != top.FieldsValue["f08"]:
        raise ValueError("generated prism requires its actual shared header counter")
    light = None
    if enabled:
        allocator = PersistentIds(before_next)
        target = FeatureTarget(**specification["feature_target"])
        light = AttachAmbientMut(root, AmbientInput(**specification["ambient"]), target, allocator, model_second)
        SetCfgStampMut(current, allocator)
        header.FieldsValue["f08"] = top.FieldsValue["f08"] = allocator.NextValue
    config_bytes, config = WriteConfigMut(root, 19000, header)
    resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                            19000, config.MapValue, link.ResolvedValue.ContextValue)
    streams = archive.streams | {
        "Header2": WriteHeadGraph(top, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
        "Contents/Config-0": config_bytes,
        "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
        "Contents/Config-0-ResolvedFeatures": resolved_bytes,
    }
    if not enabled and streams != archive.streams:
        raise ValueError("SDK no-light lane changed fresh research source streams")
    after_flags = (root.FieldsValue["f0c"], root.FieldsValue["f1e0"].FieldsValue["f0c"])
    if after_flags != before_flags:
        raise ValueError("authored lighting must not modify part or folder update flags")
    rows = root.FieldsValue["f1e0"].FieldsValue["f60"]["list"]["items"]
    if enabled and (len(rows) != 1 or rows[0]["o"] is not light or light.FieldsValue["f08"] != before_next):
        raise ValueError("typed ambient lost its actual folder or allocator identity")
    if not enabled and rows:
        raise ValueError("no-light prism has an unrequested environment member")
    return streams, {
        "ambient_present": enabled,
        "intentional_lighting_change": enabled,
        "ordinary_default_lighting_parity": False,
        "light_id": None if light is None else light.FieldsValue["f08"],
        "light_name": None if light is None else light.FieldsValue["f18"].FieldsValue["f08"],
        "original_root_ids": before_ids,
        "original_next_id": before_next,
        "next_id": header.FieldsValue["f08"],
        "part_flags": after_flags[0],
        "folder_flags": after_flags[1],
        "owner_flags_unchanged": True,
        "config_map_counter": config.MapValue.CounterValue,
        "resolved_map_counter": resolved.MapValue.CounterValue,
        "usage": {"read_config": link.ConfigValue.ReportValue, "read_resolved": link.ResolvedValue.ReportValue,
                  "write_config": config.ReportValue, "write_resolved": resolved.ReportValue},
    }
