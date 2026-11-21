from dataclasses import replace

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import (
    MakeMgrHeader,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KPartitionStream,
    KResolvedFeaturesStream,
)


def emit_attached_part(candidate, partition=None):
    cmgr = candidate.SystemValue.ManagerValue
    manager_header = MakeMgrHeader(cmgr, candidate.ManagerHeader.FieldsValue["f60"])
    config, graph = WriteConfigMut(
        candidate.SystemValue.RootValue, 19000, candidate.HeaderValue
    )
    resolved, resolved_graph = WriteResolMut(
        candidate.ResolvedValue.RootsValue,
        None,
        19000,
        graph.MapValue,
        {
            "model_compressed_stream": 1,
            "model_is_part": 1,
            "cmgr_f658": cmgr.FieldsValue["f658"],
        },
    )
    streams = candidate.StreamsValue | {
        "Contents/Config-0": config,
        KResolvedFeaturesStream: resolved,
        "Contents/Config-0-ModelHeader": WriteHeadGraph(candidate.HeaderValue, 19000),
        "Header2": WriteHeadGraph(candidate.TopHeader, 19000),
        "Contents/CMgr": WriteCmgrMut(cmgr, 19000),
        "Contents/CMgrHdr2": WriteMgrHeader(manager_header, 19000)[0],
    }
    if partition is not None:
        streams[KPartitionStream] = partition
    return replace(
        candidate,
        ManagerHeader=manager_header,
        ConfigValue=graph,
        ResolvedValue=resolved_graph,
        StreamsValue=streams,
        BytesValue=BuildSldprt(streams, FormatVersion=4),
    )
