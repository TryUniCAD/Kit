from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckThruRoots import (
    CheckThruRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckRevRoots import (
    CheckRevRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

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


# the native cabinet insertion policy must not reorder an unrelated authored feature layout
def ReadRootOrder(
    LinkValue: NativeLink,
    NodesValue: Mapping[int, ArchiveNode],
    *,
    TwoStocks: bool = False,
) -> tuple[ArchiveNode, ...]:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    RootsValue = tuple(NodesValue.values())
    Cabinets = tuple(
        NodeValue
        for NodeValue in RootsValue
        if NodeValue.ClassValue.NameValue == "moDetailCabinet_c"
    )
    Ordinary = tuple(NodeValue for NodeValue in RootsValue if NodeValue not in Cabinets)
    if len(Cabinets) != 1:
        raise ValueError("part presentation has an unqualified root layout")
    RootKinds = tuple(NodeValue.ClassValue.NameValue for NodeValue in Ordinary)
    if TwoStocks:
        if RootKinds != (
            *KOrdinaryRoots,
            "moProfileFeature_c",
            "moICE_c",
            "moProfileFeature_c",
            "moICE_c",
        ):
            raise ValueError(
                "selected two stock presentation has an alternate root layout"
            )
        CheckTreeAlias(LinkValue, RootsValue)
    elif RootKinds != KOrdinaryRoots:
        if Ordinary and Ordinary[-1].ClassValue.NameValue == "moRevolution_c":
            CheckRevRoots(LinkValue, Ordinary, KOrdinaryRoots)
        else:
            CheckThruRoots(LinkValue, NodesValue, Ordinary, KOrdinaryRoots)
    if RootsValue.index(Cabinets[0]) not in (6, 12):
        raise ValueError("authored cabinet placement is outside the ordinary profile")
    if ModelValue.FieldsValue.get("f1e0") is not Ordinary[8]:
        raise ValueError("part environment root lacks its actual model binding")
    return Ordinary[:6] + Cabinets + Ordinary[6:]
