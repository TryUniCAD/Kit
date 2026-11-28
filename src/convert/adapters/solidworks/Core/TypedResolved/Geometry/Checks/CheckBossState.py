from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# all analytic create bosses must reject additional merge selections geometry and body modifier state
def CheckBossState(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if (
        Fields.get("f28") != 0x40000000 | 0x140
        or Fields.get("f810") != -1
        or Fields.get("f838") != 0.0
    ):
        raise ValueError("cache free prism requires its ordinary create boss mode")
    if (
        Fields.get("f538") is not None
        or Fields.get("f6e0") is not None
        or Fields.get("f758") is not None
        or Fields.get("f7a0") != 0
    ):
        raise ValueError("cache free prism has additional extrusion geometry state")
    if (
        not IsLineState(Fields.get("f368"))
        or not IsLineState(Fields.get("f388"))
        or not IsLineState(Fields.get("f780"))
    ):
        raise ValueError("cache free prism has selected geometry or body references")
