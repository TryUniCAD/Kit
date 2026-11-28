from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature


# keyword cache labels must not change modeling feature classifications after a native save
def BindTreeRoot(Feature: NativeFeature, NodeValue: ArchiveNode) -> NativeFeature:
    return ReplaceValue(
        Feature,
        kind=NodeValue.ClassValue.NameValue.removeprefix("mo").removesuffix("_c"),
        properties={
            **Feature.properties,
            "solidworks_cached_type": Feature.kind,
        },
    )
