from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KGhostPartition
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.BindSwGhosts import (
    BindSwGhosts,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import (
    ReadSwPick,
    ReadSwProfile,
    SwReadProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry


# portable projection uses the actual ordered drivers and source nodes retained by the typed read
@DataClass(frozen=True, slots=True)
class SwReadState:
    IntentValue: SweepIntent
    LinkValue: NativeLink
    FeatureValue: ArchiveNode
    SectionValue: SwReadProfile
    PathValue: SwReadProfile
    DatumValues: tuple[ArchiveNode, ...]
    ConfigValue: ArchiveNode
    DensityValue: ArchiveNode


# both selected curves must agree with the actual ghost users and embedded section
def CheckSwPicks(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    SweepValue: ArchiveNode,
    SectionValue: SwReadProfile,
    PathValue: SwReadProfile,
) -> None:
    DataValue = NativeRecord(SweepValue.FieldsValue.get("f820"))
    SectionPick = RequireNative(ReadSwRow(DataValue.get("f2c0")), "moGeneralCurveRef_w")
    ContactValue = RequireNative(ReadSwRow(DataValue.get("f2e0")), "moWireContact_c")
    PathPick = RequireNative(ContactValue.FieldsValue.get("fe8"), "moGeneralCurveRef_w")
    SectionId = ReadSwPick(LinkValue, SectionPick, SectionValue.FeatureValue)
    PathId = ReadSwPick(LinkValue, PathPick, PathValue.FeatureValue)
    if (
        SectionId == PathId
        or SectionPick is PathPick
        or NativeRecord(SectionPick.FieldsValue.get("fc8")).get("CircleValue")
        != SectionValue.CurveValue
        or PathPick.FieldsValue.get("has_fc8") != 0
    ):
        raise ValueError(
            "SOLIDWORKS sweep picks disagree with their distinct live contours"
        )
    BindSwGhosts(
        Archive.require(KGhostPartition),
        LinkValue.ConfigValue.RootValue,
        SweepValue,
        PathId,
        SectionId,
    )


# source location and epoch belong to the typed header and density to the actual part
def ReadSwIntent(
    LinkValue: NativeLink, CircleValue: CircleGeometry, PathValue: ArcGeometry
) -> tuple[SweepIntent, ArchiveNode]:
    HeaderValue = LinkValue.ConfigValue.HeaderValue.FieldsValue
    FileValue = GetFileRef(HeaderValue.get("f38")).PathValue
    EpochValue = HeaderValue.get("f70")
    if type(EpochValue) is not int:
        raise ValueError("SOLIDWORKS sweep ModelHeader lacks its saved epoch")
    PartValue = LinkValue.ConfigValue.RootValue
    Material = RequireNative(PartValue.FieldsValue.get("f1420"), "moMaterial_c")
    DensityValue = RequireNative(
        Material.FieldsValue.get("f08"), "moDensityParameter_c"
    )
    Density = RequireScalar(DensityValue.FieldsValue.get("f58"))
    return (
        SweepIntent(
            PureWindowsPath(FileValue).stem,
            CircleValue,
            PathValue,
            Density,
            RequirePartPath(FileValue, EpochValue),
        ),
        DensityValue,
    )


# complete archive ownership must come from the same parsed graph before projection can begin
def ReadSwState(Archive: SldprtArchive) -> SwReadState:
    LinkValue = ReadNativeLink(Archive, 0, ReadSweeps=True)
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
        LinkValue, RequireNative(SectionNode, "moProfileFeature_c"), NodeValues, True
    )
    PathValue = ReadSwProfile(
        LinkValue, RequireNative(PathNode, "moProfileFeature_c"), NodeValues, False
    )
    CircleValue, ArcValue = SectionValue.CurveValue, PathValue.CurveValue
    if (
        type(CircleValue) is not CircleGeometry
        or type(ArcValue) is not ArcGeometry
        or SectionValue.DriverValue.NativeId == PathValue.DriverValue.NativeId
    ):
        raise ValueError(
            "SOLIDWORKS sweep requires an independent diameter and path radius"
        )
    CheckSwPicks(Archive, LinkValue, SweepValue, SectionValue, PathValue)
    IntentValue, DensityValue = ReadSwIntent(LinkValue, CircleValue, ArcValue)
    DatumValues = tuple(
        Value for Value in RootsValue if Value.ClassValue.NameValue == "moRefPlane_c"
    )
    ManagerValue = LinkValue.ManagerValue
    if ManagerValue is None:
        raise ValueError("SOLIDWORKS sweep lacks its independent configuration manager")
    (ConfigValue,) = (
        Value
        for EntryValue in ManagerValue.MapValue.EntriesValue
        if isinstance(Value := EntryValue.EntryValue, ArchiveNode)
        and Value.ClassValue.NameValue == "moPartConfiguration_c"
    )
    return SwReadState(
        IntentValue,
        LinkValue,
        SweepValue,
        SectionValue,
        PathValue,
        DatumValues,
        ConfigValue,
        DensityValue,
    )
