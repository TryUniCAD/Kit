from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# actual body selectors share their component stock ownership and lineage across first generation and later native saves
def CheckCutWrapper(
    RootValue: ArchiveNode,
    BossValue: ArchiveNode,
    CutValue: ArchiveNode,
    AtomId: int,
    *,
    IsCold: bool = False,
    UseProducerSentinel: bool = False,
) -> None:
    Wrapper = ReadSingleNode(
        CutValue.FieldsValue.get("f548"), "moCompSolidBody_c"
    ).FieldsValue
    Component = RequireNative(Wrapper.get("f58"), "moUnitComponent_c")
    Lineage = NativeRows(Wrapper.get("f110"))
    Producer = -1 if UseProducerSentinel else NativeNodeId(BossValue)
    if (
        Wrapper.get("f108") != Producer
        or Wrapper.get("f18") != AtomId
        or Wrapper.get("f1c") != AtomId
        or Wrapper.get("n110") != 1
        or tuple(RowValue.get("v") for RowValue in Lineage) != (AtomId,)
        or Component.FieldsValue.get("owner") is not RootValue
    ):
        raise ValueError("cut selection wrapper differs from the consumed boss atom")
    if IsCold and (
        Component.FieldsValue.get("has_ext") != 0
        or Wrapper.get("ff0") is not None
        or Wrapper.get("f100") != 0
        or Wrapper.get("f104") != 0
    ):
        raise ValueError("cold cut selection has an external or cached topology owner")
