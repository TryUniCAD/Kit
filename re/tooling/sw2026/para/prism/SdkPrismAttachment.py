from dataclasses import dataclass, replace

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import MakeStockAtom
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KPartitionStream, KResolvedFeaturesStream
from downstream.lighting.AmbientInput import AmbientInput
from downstream.lighting.AttachAmbientMut import AttachAmbientMut
from para.cylinder.CylinderAttachment import bind_features, mark_node
from para.prism.SdkPrismPartition import sdk_prism
from para.rectangle.Allocate import require
from para.rectangle.ArchiveAttachment import REBUILT_EXTRUSION_STATUS


@dataclass(frozen=True)
class AttachedPrism:
    candidate: object
    prism: object


def install_light(candidate, intent, event_second):
    config_header, top_header = candidate.HeaderValue, candidate.TopHeader
    index = config_header.FieldsValue["f08"]
    require(index == top_header.FieldsValue["f08"], "the part headers must share the actual ID cursor")
    allocator = PersistentIds(index)
    AttachAmbientMut(candidate.SystemValue.RootValue, AmbientInput(**intent["ambient"]),
                     FeatureTarget(**intent["feature_target"]), allocator, event_second)
    SetCfgStampMut(candidate.CurrentConfig, allocator)
    config_header.FieldsValue["f08"] = top_header.FieldsValue["f08"] = allocator.NextValue


def attach_sdk_prism(candidate, session, feature_events, appearance, light, previous_faces=0, *, downstream=None):
    require(KPartitionStream not in candidate.StreamsValue, "the candidate already owns a partition")
    root = candidate.SystemValue.RootValue
    model = root.FieldsValue
    manager = model["fd88"]
    boss = candidate.BossValue.FeatureValue
    feature = boss.FieldsValue
    require(not model["ffe0"] and model.get("fe38") is None and feature.get("f538") is None
            and not any(feature[key] for key in ("has_f528", "has_f530", "n494", "has_f3d0")),
            "the candidate already owns live body or extrusion output state")
    prism = sdk_prism(candidate, session, appearance, previous_faces, downstream=downstream)
    atom = MakeStockAtom(boss, prism.atom_id)
    tag, = prism.tracking.body_fields["BODY_MATCH"]
    atom.FieldsValue.update(f180=tag, f1b0=tag, f188=1)
    outputs = [{"o": atom}]
    manager.update(f260=prism.atom_id, n6c=len(outputs), fa8=19000, atoms=outputs)
    model.update(fe38=mark_node(prism.marks.activation), f1010=1,
                 ffe0=[{"k": atom, "v": int(atom.FieldsValue["f170"] != 0)}], nff4=len(outputs))
    feature.update(
        has_f528=1, f528={"n": len(outputs), "items": [{"o": atom}]},
        n494=len(outputs), f498=[{"v": atom.FieldsValue["f140"]}],
        has_f3d0=1, f3d0=mark_node(prism.marks.selected),
        f3c0=0, f3c8=0, f580=0, f540=REBUILT_EXTRUSION_STATUS,
    )
    bind_features(candidate, session, feature_events)
    for header in (candidate.HeaderValue, candidate.TopHeader):
        header.FieldsValue.update(f40=prism.updates.saved_update, f44=prism.updates.saved_body,
                                  f48=session.update_second)
    candidate.CurrentConfig.FieldsValue["f860"] = prism.updates.saved_update
    if light is not None:
        install_light(candidate, light, session.update_second)
    cmgr = candidate.SystemValue.ManagerValue
    manager_header = MakeMgrHeader(cmgr, candidate.ManagerHeader.FieldsValue["f60"])
    config, config_graph = WriteConfigMut(root, 19000, candidate.HeaderValue)
    resolved, resolved_graph = WriteResolMut(
        candidate.ResolvedValue.RootsValue, None, 19000, config_graph.MapValue,
        {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": cmgr.FieldsValue["f658"]},
    )
    streams = candidate.StreamsValue | {
        "Contents/Config-0": config,
        KResolvedFeaturesStream: resolved,
        "Contents/Config-0-ModelHeader": WriteHeadGraph(candidate.HeaderValue, 19000),
        "Header2": WriteHeadGraph(candidate.TopHeader, 19000),
        "Contents/CMgr": WriteCmgrMut(cmgr, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(manager_header, 19000)[0],
        KPartitionStream: prism.stream(),
    }
    attached = replace(candidate, ManagerHeader=manager_header, ConfigValue=config_graph,
                       ResolvedValue=resolved_graph, StreamsValue=streams,
                       BytesValue=BuildSldprt(streams, FormatVersion=4))
    return AttachedPrism(attached, prism)
