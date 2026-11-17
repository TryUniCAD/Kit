from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# grammar metadata must expose linked prerequisites without claiming their unresolved semantic admission
def DescribeConfig(
    GraphValue: ConfigGraph, ManagerInfo: Mapping[str, object]
) -> Mapping[str, object]:
    DirectNodes = HeaderRefNodes(GraphValue.HeaderValue, GraphValue.VersionValue)
    IndexValues = {
        id(Entry.EntryValue): Entry.IndexValue
        for Entry in GraphValue.MapValue.EntriesValue
    }
    ManagerWord = (
        ManagerInfo.get("resolved_body_mapping_context")
        if ManagerInfo.get("status") == "complete"
        else None
    )
    return {
        "status": "complete",
        "archive_version": GraphValue.VersionValue,
        "model_class": GraphValue.RootValue.ClassValue.NameValue,
        "map_base": GraphValue.MapBase,
        "map_counter": GraphValue.MapValue.CounterValue,
        "object_count": sum(
            isinstance(Entry.EntryValue, ArchiveNode)
            for Entry in GraphValue.MapValue.EntriesValue
        ),
        "header_aliases": tuple(
            {
                "ordinal": Index,
                "object_index": IndexValues[id(NodeValue)],
                "class": NodeValue.ClassValue.NameValue,
            }
            for Index, NodeValue in enumerate(DirectNodes)
        ),
        "usage": GraphValue.ReportValue,
        "resolved_dependency": {
            "model_compressed_stream": 1,
            "model_is_part": int(
                GraphValue.RootValue.ClassValue.NameValue == "moPart_c"
            ),
            "cmgr_f658": ManagerWord,
            "manager_map_base": 1,
            "manager_context_available": type(ManagerWord) is int,
            "manager_map_seeded_configuration": False,
        },
        "full_linked_graph": False,
        "resolved_body_codec_promoted": False,
    }
