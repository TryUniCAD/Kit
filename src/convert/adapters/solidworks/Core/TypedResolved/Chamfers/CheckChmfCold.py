from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# each typed dimension chain is disjoint and belongs to the actual feature slots in archive order
def CheckChmfDrives(Owners: ChmfOwners) -> None:
    Drivers = (Owners.Distance, Owners.AngleValue)
    Nodes = tuple(NodeValue for Driver in Drivers for NodeValue in ChmfDimNodes(Driver))
    IdsValue = tuple(Driver.DimensionNode.FieldsValue.get("f50") for Driver in Drivers)
    OwnerId = NativeNodeId(Owners.FeatureValue)
    FirstId, OtherId = IdsValue
    if (
        len(set(Nodes)) != 8
        or type(FirstId) is not int
        or type(OtherId) is not int
        or not 0 < FirstId < OtherId < OwnerId
        or any(
            NodeValue.IndexValue is None
            or Owners.FeatureValue.IndexValue is None
            or NodeValue.IndexValue <= Owners.FeatureValue.IndexValue
            for NodeValue in Nodes
        )
    ):
        raise ValueError(
            "chamfer has alternate dimension order or shared driver ownership"
        )


# the bound editing chain contains the actual archived display handle value and parameter
def ChmfDimNodes(Driver: ChmfDriver) -> tuple[ArchiveNode, ...]:
    return (
        Driver.DisplayNode,
        Driver.HandleNode,
        Driver.DimensionNode,
        Driver.ParameterNode,
    )


# the actual component wrappers must retain independent local unqualified point hints
def CheckChmfWrap(LinkValue: NativeLink, Feature: ArchiveNode) -> None:
    Fields = Feature.FieldsValue
    ListValue = RequireNative(Fields.get("f888"), "suObList").FieldsValue
    (RowValue,) = NativeRows(ListValue.get("items"))
    Selected = RequireNative(RowValue.get("o"), "moCompEdge_c")
    Detached = RequireNative(Fields.get("f8a8"), "moCompEdge_c")
    Parts = tuple(
        RequireNative(Value.FieldsValue.get("f58"), "moUnitComponent_c")
        for Value in (Selected, Detached)
    )
    if (
        ListValue.get("n") != 1
        or Parts[0] is Parts[1]
        or NativeRecord(NativeRecord(Fields.get("f880")).get("ff0")).get("n") != 1
        or any(
            NodeValue.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
            or NodeValue.FieldsValue.get("has_ext") != 0
            for NodeValue in Parts
        )
        or any(
            Value.FieldsValue.get("has_alias") != 0
            or not IsLineState(Value.FieldsValue.get("f130"))
            or any(
                NativeRecord(Value.FieldsValue.get(NameValue))
                != dict.fromkeys("xyz", 0.0)
                for NameValue in ("f158", "f170")
            )
            for Value in (Selected, Detached)
        )
    ):
        raise ValueError(
            "cold chamfer has a foreign component or alternate selected point hints"
        )
    CheckTreeAlias(LinkValue, Parts)


# fresh signed mode admits only empty optional modifier state outside the linked stock atom
def CheckChmfCold(LinkValue: NativeLink, Owners: ChmfOwners) -> None:
    Fields = Owners.FeatureValue.FieldsValue
    if (
        Fields.get("f8c8") != {"n": 0, "items": []}
        or Fields.get("f758") is not None
        or Fields.get("f6e0") is not None
        or Fields.get("f4a0") != 1
        or any(Fields.get(NameValue) != 0 for NameValue in KAtomWords)
        or any(not IsLineState(Fields.get(NameValue)) for NameValue in KAtomLists)
        or any(
            Fields.get(NameValue) != {"n": 0, "items": []}
            for NameValue in ("f368", "f388", "f780")
        )
    ):
        raise ValueError(
            "fresh chamfer carries unqualified stored selector or modifiers"
        )
    CheckChmfDrives(Owners)
    CheckChmfWrap(LinkValue, Owners.FeatureValue)
