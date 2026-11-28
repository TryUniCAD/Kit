from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the persisted explicit wrapper determines which historical stock the cut acts on
def ReadColdSelect(
    LinkValue: NativeLink,
    OwnersValue: tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner],
    AtomIds: tuple[int, int],
) -> tuple[int, ArchiveNode]:
    FirstStock, SecondStock, CutValue = OwnersValue
    FieldsValue = CutValue.NodeValue.FieldsValue
    if FieldsValue.get("f544") != 1 or FieldsValue.get("has_f548") != 1:
        raise ValueError(
            "pre-rebuild through cut requires one explicit stock selection"
        )
    WrapperValue = ReadSingleNode(FieldsValue.get("f548"), "moCompSolidBody_c")
    ProducerId = WrapperValue.FieldsValue.get("f108")
    StockNodes = (FirstStock.NodeValue, SecondStock.NodeValue)
    Matches = tuple(
        Index
        for Index, NodeValue in enumerate(StockNodes)
        if type(ProducerId) is int and ProducerId == NativeNodeId(NodeValue)
    )
    if len(Matches) != 1:
        raise ValueError(
            "cut selector does not identify an actual earlier stock producer"
        )
    (Selected,) = Matches
    CheckCutWrapper(
        LinkValue.ConfigValue.RootValue,
        StockNodes[Selected],
        CutValue.NodeValue,
        AtomIds[Selected],
        IsCold=True,
    )
    Component = RequireNative(WrapperValue.FieldsValue.get("f58"), "moUnitComponent_c")
    CheckTreeAlias(LinkValue, (WrapperValue, Component))
    return Selected, WrapperValue
