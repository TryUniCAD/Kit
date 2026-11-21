from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# inherited objects retain configuration positions while newly allocated resolved objects own resolved positions
def NativeNodeSpan(
    LinkValue: NativeLink, NodeValue: ArchiveNode
) -> Mapping[str, object]:
    IsInherited = any(
        EntryValue.EntryValue is NodeValue
        for EntryValue in LinkValue.ConfigValue.MapValue.EntriesValue
    )
    return {
        "stream": LinkValue.ConfigName if IsInherited else LinkValue.StreamName,
        "object_index": NodeValue.IndexValue,
        "offset": NodeValue.StartOffset,
        "end": NodeValue.EndOffset,
        "class": NodeValue.ClassValue.NameValue,
        "field_span": False,
    }
