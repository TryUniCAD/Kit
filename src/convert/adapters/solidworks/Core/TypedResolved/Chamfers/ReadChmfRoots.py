from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckExtras import (
    CheckExtras,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ConfigHelpers import (
    ReadConfigHelp,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.OwnedRows import (
    ReadOwnedRows,
)


# presentation normalization is restricted to the measured ordinary single profile part ownership sequence
KOrdinaryRoots = (
    "moCommentsFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moDocsFolder_c",
    "moSurfaceBodyFolder_c",
    "moSolidBodyFolder_c",
    "moEnvFolder_c",
    "moInkMarkupFolder_c",
    "moEqnFolder_c",
    "moMaterialFolder_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moOriginProfileFeature_c",
    "moProfileFeature_c",
    "moExtrusion_c",
)


# presentation rooting keeps the whole ordinary stock prefix and its one actual new modeling feature
def ReadChmfRoots(
    LinkValue: NativeLink,
    ModelValue: NativeModel,
    ChmfValue: ArchiveNode,
) -> tuple[tuple[ArchiveNode, ...], dict[int, ArchiveNode]]:
    Resolved = LinkValue.ResolvedValue
    if (
        Resolved.ExtraFields != {"n": 0, "fcd8": []}
        or Resolved.RootsValue[-1] is not ChmfValue
    ):
        raise ValueError(
            "chamfer requires the exact fresh end of the ordinary stock root sequence"
        )
    Prefix = ReplaceValue(
        LinkValue,
        ResolvedValue=ReplaceValue(Resolved, RootsValue=Resolved.RootsValue[:-1]),
    )
    Nodes = IndexFeatures(Prefix)
    Roots = (*ReadChmfPrefix(Prefix, Nodes), ChmfValue)
    NativeId = NativeNodeId(ChmfValue)
    if NativeId in Nodes:
        raise ValueError(
            "chamfer feature repeats an actual earlier stock root identity"
        )
    Nodes[NativeId] = ChmfValue
    Members: tuple[ArchiveNode, ...] = ()
    for NodeValue in Roots:
        if NodeValue.ClassValue.NameValue in ("moDetailCabinet_c", "moEnvFolder_c"):
            _, Owned = ReadOwnedRows(LinkValue, NodeValue)
            Members += Owned
    CheckExtras(ModelValue, Roots, Members, ReadConfigHelp(LinkValue))
    if set(Nodes) != {
        Feature.object_id for Feature in ModelValue.features
    }:
        raise ValueError(
            "chamfer cannot project unrepresented alternate feature presentation"
        )
    CheckTreeAlias(LinkValue, Roots)
    return Roots, Nodes


# only the ordinary single blind stock can precede the scoped cold modifier
def ReadChmfPrefix(
    LinkValue: NativeLink, NodesValue: Mapping[int, ArchiveNode]
) -> tuple[ArchiveNode, ...]:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    RootsValue = tuple(NodesValue.values())
    Cabinets = tuple(
        NodeValue for NodeValue in RootsValue
        if NodeValue.ClassValue.NameValue == "moDetailCabinet_c"
    )
    Ordinary = tuple(NodeValue for NodeValue in RootsValue if NodeValue not in Cabinets)
    if (
        len(Cabinets) != 1
        or tuple(NodeValue.ClassValue.NameValue for NodeValue in Ordinary) != KOrdinaryRoots
        or RootsValue.index(Cabinets[0]) not in (6, 12)
        or ModelValue.FieldsValue.get("f1e0") is not Ordinary[8]
    ):
        raise ValueError("chamfer has an unqualified ordinary stock root layout")
    return Ordinary[:6] + Cabinets + Ordinary[6:]
