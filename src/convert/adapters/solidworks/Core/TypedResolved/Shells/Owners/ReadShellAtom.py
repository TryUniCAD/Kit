from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# current shell atom ownership links the original creator and actual last modifier
def ReadShellAtom(
    LinkValue: NativeLink, StockNode: ArchiveNode, ShellNode: ArchiveNode
) -> ArchiveNode:
    AtomValue = ReadMgrAtom(LinkValue)
    AtomFields, ShellFields = AtomValue.FieldsValue, ShellNode.FieldsValue
    StampValue = AtomFields.get("f180")
    if (
        ReadOutputAtom(StockNode) is not AtomValue
        or ShellFields.get("f538") is not AtomValue
        or AtomFields.get("f12c") != NativeNodeId(StockNode)
        or AtomFields.get("f130") != NativeNodeId(ShellNode)
        or AtomFields.get("f18") is not None
        or AtomFields.get("f18c") != 1
        or type(StampValue) is not int
        or StampValue <= 0
        or any(
            Value != StampValue
            for Value in (
                AtomFields.get("f1b0"),
                ShellFields.get("f3c0"),
                ShellFields.get("f580"),
            )
        )
    ):
        raise ValueError("SOLIDWORKS shell has a different active atom or producer")
    Manager = NativeRecord(LinkValue.ConfigValue.RootValue.FieldsValue.get("fd88"))
    AtomId = AtomFields.get("f140")
    if type(AtomId) is not int or AtomId <= 0 or Manager.get("f260") != AtomId:
        raise ValueError("SOLIDWORKS shell atom differs from its configuration manager")
    if (
        StockNode.FieldsValue.get("f498") != [{"v": AtomId}]
        or StockNode.FieldsValue.get("n494") != 1
        or ShellFields.get("n494") != 0
        or ShellFields.get("has_f528") != 0
        or ShellFields.get("has_f530") != 0
    ):
        raise ValueError("SOLIDWORKS shell has alternate selected or result atom state")
    CheckTreeAlias(LinkValue, (StockNode, ShellNode, AtomValue))
    return AtomValue


# the active shell mark belongs to the selected modeled feature after the stock
def ReadShellMarks(
    LinkValue: NativeLink, StockNode: ArchiveNode, ShellNode: ArchiveNode
) -> tuple[int, int, int]:
    MarksValue = (
        RequireNative(
            LinkValue.ConfigValue.RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c"
        ),
        RequireNative(StockNode.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
        RequireNative(ShellNode.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
    )
    CheckTreeAlias(LinkValue, MarksValue)
    Activation, StockMark, FinalMark = tuple(
        Value.FieldsValue.get("f18") for Value in MarksValue
    )
    if (
        StockNode.FieldsValue.get("has_f3d0") != 1
        or ShellNode.FieldsValue.get("has_f3d0") != 1
        or type(Activation) is not int
        or type(StockMark) is not int
        or type(FinalMark) is not int
        or not 0 < Activation < StockMark < FinalMark
    ):
        raise ValueError("SOLIDWORKS shell lacks distinct saved partition marks")
    return Activation, StockMark, FinalMark
