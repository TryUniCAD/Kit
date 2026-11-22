from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.CheckSwPicks import (
    CheckSwPicks,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import (
    ReadSwProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)


# density belongs to the live material parameter and must never be inferred from the saved body alone
def ReadSwDensity(LinkValue: NativeLink) -> ArchiveNode:
    PartValue = LinkValue.ConfigValue.RootValue
    Material = RequireNative(PartValue.FieldsValue.get("f1420"), "moMaterial_c")
    return RequireNative(Material.FieldsValue.get("f08"), "moDensityParameter_c")


# the separate manager chooses the actual configuration for the linked part
def ReadSwConfig(LinkValue: NativeLink) -> ArchiveNode:
    ManagerValue = LinkValue.ManagerValue
    if ManagerValue is None:
        raise ValueError("SOLIDWORKS sweep lacks its independent configuration manager")
    (ConfigValue,) = (
        Value
        for EntryValue in ManagerValue.MapValue.EntriesValue
        if isinstance(Value := EntryValue.EntryValue, ArchiveNode)
        and Value.ClassValue.NameValue == "moPartConfiguration_c"
    )
    return ConfigValue


# complete archive ownership must come from the same parsed graph before projection can begin
def ReadSwGraph(Archive: SldprtArchive) -> SwReadGraph:
    LinkValue = ReadNativeLink(Archive, 0, SavedSweep=True)
    RootsValue = tuple(
        RequireNative(Value) for Value in LinkValue.ResolvedValue.RootsValue
    )
    NodeValues = {NativeNodeId(Value): Value for Value in RootsValue}
    (SweepValue,) = (
        Value for Value in RootsValue if Value.ClassValue.NameValue == "moSweep_c"
    )
    SectionNode, PathNode = ReadParents(SweepValue)
    if len(NodeValues) != len(RootsValue) or RootsValue[-3:] != (
        SectionNode,
        PathNode,
        SweepValue,
    ):
        raise ValueError(
            "SOLIDWORKS sweep does not own two actual earlier sketch roots"
        )
    SectionValue = ReadSwProfile(
        LinkValue,
        RequireNative(SectionNode, "moProfileFeature_c"),
        NodeValues,
        True,
    )
    PathValue = ReadSwProfile(
        LinkValue,
        RequireNative(PathNode, "moProfileFeature_c"),
        NodeValues,
        False,
    )
    if SectionValue.DriverValue.NativeId == PathValue.DriverValue.NativeId:
        raise ValueError(
            "SOLIDWORKS sweep requires an independent diameter and path radius"
        )
    DatumValues = tuple(
        Value for Value in RootsValue if Value.ClassValue.NameValue == "moRefPlane_c"
    )
    GraphValue = SwReadGraph(
        LinkValue,
        SweepValue,
        SectionValue,
        PathValue,
        DatumValues,
        ReadSwConfig(LinkValue),
        ReadSwDensity(LinkValue),
    )
    CheckSwPicks(Archive, GraphValue)
    return GraphValue
