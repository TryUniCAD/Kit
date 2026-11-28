from typing import cast as CastValue

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadRows,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceTree import (
    ReadSourceTree,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.document.Models.DocumentModel import CadDocument


# independently supplied typed archives must still agree with the complete retained source root identity and presentation evidence
def CheckThruLink(DocumentValue: CadDocument, LinkValue: NativeLink) -> None:
    if (
        type(LinkValue) is not NativeLink
        or LinkValue.ConfigName != "Contents/Config-0"
        or LinkValue.ConfigValue.VersionValue != 19000
        or LinkValue.ResolvedValue.VersionValue != 19000
    ):
        raise ValueError(
            "source configuration intent requires the actual version 19000 Config-0 link"
        )
    TreeValue = ReadSourceTree(DocumentValue)
    Features = IndexFeatures(LinkValue)
    RawIds = TreeValue.get("root_ids")
    if not isinstance(RawIds, (tuple, list)):
        raise ValueError("source presentation lacks its actual root identities")
    RootIds = tuple(CastValue(tuple[object, ...] | list[object], RawIds))
    if tuple(Features) != RootIds:
        raise ValueError(
            "source root identities differ from the retained complete source"
        )
    RowsValue = ReadRows(TreeValue.get("rows"))
    RootRows = tuple(
        EntryValue for EntryValue in RowsValue if EntryValue.get("parent_id") is None
    )
    if tuple(
        FieldInt(EntryValue, "native_object_id") for EntryValue in RootRows
    ) != tuple(Features):
        raise ValueError(
            "source root presentation order differs from its actual linked objects"
        )
    for EntryValue in RootRows:
        NodeValue = Features[FieldInt(EntryValue, "native_object_id")]
        if NodeValue.ClassValue.NameValue != FieldText(
            EntryValue, "class"
        ) or ReadNativeName(NodeValue) != FieldText(EntryValue, "name"):
            raise ValueError(
                "source root class or caption differs from its actual linked owner"
            )
