from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import (
    ReadBodyOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfMode import (
    CheckChmfMode,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDrives import (
    ReadChmfDrives,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfPick import (
    ReadChmfPick,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# only saved chamfers may bind physical activation marks to the actual three owners
def ReadChmfMarks(
    RootValue: ArchiveNode,
    StockValue: ArchiveNode,
    Feature: ArchiveNode,
    ColdValue: bool,
) -> tuple[ArchiveNode, ...]:
    if ColdValue:
        if (
            "fe38" not in RootValue.FieldsValue
            or RootValue.FieldsValue["fe38"] is not None
            or any(
                NodeValue.FieldsValue.get("has_f3d0") != 0
                or "f3d0" in NodeValue.FieldsValue
                for NodeValue in (StockValue, Feature)
            )
        ):
            raise ValueError("fresh chamfer contains saved rollback ownership")
        return ()
    return (
        RequireNative(RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c"),
        RequireNative(StockValue.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
        RequireNative(Feature.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
    )


# only the actual single preceding stock and its inherited modified atom authorize selected chamfer ownership
def ReadChmfOwn(
    LinkValue: NativeLink, *, ColdValue: bool = False, AllowDistancePair: bool = False
) -> ChmfOwners:
    RootsValue = LinkValue.ResolvedValue.RootsValue
    if len(RootsValue) < 2:
        raise ValueError("ordinary chamfer lacks actual stock and rollback owners")
    Feature = RequireNative(RootsValue[-1], "Chamfer_c")
    Fields = Feature.FieldsValue
    ModeWord = Fields.get("f8c0") if ColdValue and AllowDistancePair else 1
    if type(ModeWord) is not int:
        raise ValueError("unsupported ordinary SOLIDWORKS chamfer mode or selector")
    CheckChmfMode(Feature, ModeWord)
    StockValue = ReadBodyOwner(LinkValue, None)
    AtomValue = ReadMgrAtom(LinkValue)
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Controllers = ReadChmfMarks(RootValue, StockValue, Feature, ColdValue)
    AtomFields = AtomValue.FieldsValue
    AtomId = AtomFields.get("f140")
    if (
        RootsValue[-2] is not StockValue
        or sum(
            NodeValue is not None and NodeValue.ClassValue.NameValue == "Chamfer_c"
            for NodeValue in RootsValue
        )
        != 1
        or ReadOutputAtom(StockValue) is not AtomValue
        or Feature.FieldsValue.get("f538") is not AtomValue
        or AtomFields.get("f12c") != NativeNodeId(StockValue)
        or AtomFields.get("f130") != NativeNodeId(Feature)
        or AtomFields.get("f12c") == AtomFields.get("f130")
        or AtomFields.get("f18") is not None
        or AtomFields.get("f18c") != 1
        or type(AtomId) is not int
        or AtomId <= 0
        or any(set(NodeValue.FieldsValue) != {"f18"} for NodeValue in Controllers)
    ):
        raise ValueError("ordinary chamfer lacks actual stock and rollback owners")
    CheckTreeAlias(LinkValue, (StockValue, Feature, AtomValue, *Controllers))
    Inherited = {AtomValue} if ColdValue else {AtomValue, Controllers[0]}
    if not Inherited <= {
        EntryValue.EntryValue
        for EntryValue in LinkValue.ConfigValue.MapValue.EntriesValue
    }:
        raise ValueError(
            "ordinary chamfer lacks inherited activation or atom ownership"
        )
    Selected, Detached = ReadChmfPick(LinkValue, Feature, AtomId, ColdValue=ColdValue)
    Distance, AngleValue, SecondValue = ReadChmfDrives(LinkValue, Feature, ModeWord)
    return ChmfOwners(
        StockValue,
        Feature,
        AtomValue,
        Selected,
        Detached,
        Distance,
        AngleValue,
        Controllers,
        ModeWord,
        SecondValue,
    )
