from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# before native rebuild an explicit revolve selector uses the actual stock atom and its inherited component
def ReadColdRevPick(
    LinkValue: NativeLink,
    StockNodes: tuple[ArchiveNode, ArchiveNode],
    CutNode: ArchiveNode,
    AtomIds: tuple[int, int],
) -> tuple[int, ArchiveNode]:
    if (
        CutNode.FieldsValue.get("f544") != 1
        or CutNode.FieldsValue.get("has_f548") != 1
        or any(
            StockNode.FieldsValue.get("f544") != 1
            or StockNode.FieldsValue.get("has_f548") != 0
            or StockNode.FieldsValue.get("f548") is not None
            for StockNode in StockNodes
        )
    ):
        raise ValueError("cold revolve requires one actual earlier stock selector")
    Wrapper = ReadSingleNode(CutNode.FieldsValue.get("f548"), "moCompSolidBody_c")
    Fields = Wrapper.FieldsValue
    AtomId = Fields.get("f18")
    if (
        type(AtomId) is not int
        or AtomId not in AtomIds
        or any(
            Fields.get(Token) != 0
            for Token in ("has_fb0", "has_fb8", "has_fc0", "has_fc8", "has_fd0")
        )
    ):
        raise ValueError(
            "cold revolve selector does not identify its actual live stock"
        )
    Selected = AtomIds.index(AtomId)
    CheckCutWrapper(
        LinkValue.ConfigValue.RootValue,
        StockNodes[Selected],
        CutNode,
        AtomId,
        IsCold=True,
        UseProducerSentinel=True,
    )
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    CheckTreeAlias(LinkValue, (Wrapper, Component))
    return Selected, Wrapper
