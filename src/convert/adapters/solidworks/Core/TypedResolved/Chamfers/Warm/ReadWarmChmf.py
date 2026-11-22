from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.BuildChmfGeom import (
    ChmfPrism,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfCold import (
    CheckChmfDrives,
    CheckChmfWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    JoinChmfEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import (
    ReadChmfOwn,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRoots import (
    ReadChmfRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    EdgeChmfRows,
    ReadChmfRef,
    ReadChmfRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmStock import (
    CheckWarmStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmBody import (
    ReadWarmBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmSketch import (
    ReadWarmSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqConfig import (
    CheckEqConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedFaces import (
    CheckSavedFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved result has a counted option cache and one rollback modifier with no extra selections
def CheckWarmChmf(LinkValue: NativeLink, Owners: ChmfOwners) -> None:
    Fields = Owners.FeatureValue.FieldsValue
    Options = NativeRecord(Fields.get("f8c8"))
    RowsValue = NativeRows(Options.get("items"))
    if (
        Options.get("n") != 6
        or len(RowsValue) != 6
        or any(type(RowValue.get("v")) is not int for RowValue in RowsValue)
        or Fields.get("f28") not in (0x40000001, 0xC0000001)
        or Fields.get("f4a0") != 1
        or any(Fields.get(FieldName) is not None for FieldName in ("f758", "f6e0"))
        or any(
            Fields.get(FieldName) != int(FieldName == "has_f3d0")
            for FieldName in KAtomWords
        )
        or any(not IsLineState(Fields.get(FieldName)) for FieldName in KAtomLists)
        or any(
            not IsLineState(Fields.get(FieldName))
            for FieldName in ("f368", "f388", "f780")
        )
    ):
        raise ValueError("saved chamfer has unsupported modifier or option topology")
    CheckChmfWrap(LinkValue, Owners.FeatureValue)
    CheckChmfDrives(Owners)


# warm selection and neutral drivers are admitted only together with their actual physical body
def ReadWarmChmf(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    LinkValue: NativeLink,
) -> ChmfPartRead:
    Owners = ReadChmfOwn(LinkValue, AllowDistancePair=True)
    if Owners.ModeWord not in (2, 18):
        raise ValueError("saved chamfer mode is outside the measured distance pair")
    CheckWarmChmf(LinkValue, Owners)
    Roots, Nodes = ReadChmfRoots(
        LinkValue, ModelValue, Owners.FeatureValue, IsSaved=True
    )
    StockOp, ChmfOp = ModelValue.operations
    StockValue = ReadExtrude(LinkValue, Owners.StockValue, Nodes)
    Feature = next(
        Value for Value in ModelValue.features if Value.object_id == ChmfOp.object_id
    )
    if (
        NativeNodeId(Owners.StockValue) != StockOp.object_id
        or NativeNodeId(Owners.FeatureValue) != ChmfOp.object_id
        or NativeNodeId(StockValue.ProfileValue) != StockOp.profile_id
        or ChmfOp.dependencies != (StockOp.object_id,)
        or tuple(Value.name for Value in Feature.dimensions)
        != tuple(Value.NameValue for Value in Owners.DriversValue)
    ):
        raise ValueError(
            "saved chamfer does not own the active public operation and stock"
        )
    MgrValue = ReadCmgrMut(
        Archive.require("Contents/CMgr"), LinkValue.ConfigValue.VersionValue
    )
    CheckEqConfig(MgrValue.RootValue, "Default")
    CheckPrismRels(LinkValue.ConfigValue.RootValue, IsSaved=True)
    CheckWarmStock(LinkValue, Owners, StockValue)
    DepthValue = StockValue.RequireDepth().DepthValue.value_mm
    if DepthValue is None:
        raise ValueError("saved chamfer stock has no active blind depth")
    PlanValue, LoopValue = ReadWarmSketch(
        LinkValue, StockValue.ProfileValue, Nodes, DepthValue
    )
    Header = ReadHeaderGraph(
        Archive.require("Header2"), LinkValue.ConfigValue.VersionValue
    )
    KeysValue = ReadChmfRows(LinkValue, Owners, Header, IsSaved=True)
    FirstRole = EdgeChmfRows(Owners.SelectedRef)[0]
    FirstRef = ReadChmfRef(LinkValue, FirstRole, Owners.StockValue, Header, False)
    FileValue = RequireNative(FirstRef.FieldsValue.get("f08"), "moExtObject_c")
    CheckSavedFaces(
        Archive, LinkValue, Owners.StockValue, LoopValue, "Default", FileValue=FileValue
    )
    EdgeValue = JoinChmfEdge(PlanValue, LoopValue, KeysValue)
    Physical = ReadWarmBody(
        Archive, LinkValue, Owners, PlanValue, LoopValue, EdgeValue, KeysValue
    )
    return ChmfPartRead(
        LinkValue,
        Owners,
        StockValue,
        ChmfPrism(LinkValue, Owners, EdgeValue),
        EdgeValue,
        Roots,
        Physical,
    )


# actual marked distance modes fail strict admission on broken body or owner evidence
def TryWarmChmf(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    Settings: ReadOptions,
) -> ChmfPartRead | None:
    if (
        Settings.extract_raw_brep
        or ModelValue.active_configuration_id != 0
        or tuple(
            (Value.configuration_id, Value.name) for Value in ModelValue.configurations
        )
        != ((0, "Default"),)
        or tuple(Value.kind for Value in ModelValue.operations) != ("join", "chamfer")
        or len(ModelValue.sketches) != 1
        or ModelValue.equations
    ):
        return None
    try:
        LinkValue = ReadNativeLink(Archive, 0, ReadChamfers=True)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    RootsValue = LinkValue.ResolvedValue.RootsValue
    Feature = RootsValue[-1] if RootsValue else None
    if (
        Feature is None
        or Feature.ClassValue.NameValue != "Chamfer_c"
        or Feature.FieldsValue.get("f8c0") not in (2, 18)
        or (
            Feature.FieldsValue.get("has_f3d0") == 0
            and LinkValue.ConfigValue.RootValue.FieldsValue.get("fe38") is None
            and Feature.FieldsValue.get("f8c8") == {"n": 0, "items": []}
        )
    ):
        return None
    try:
        return ReadWarmChmf(Archive, ModelValue, LinkValue)
    except (KeyError, TypeError, ValueError, OverflowError, StopIteration) as Error:
        if Settings.strict:
            raise SldprtFormatError(
                f"saved distance chamfer ownership rejected: {Error}"
            ) from Error
        return None
