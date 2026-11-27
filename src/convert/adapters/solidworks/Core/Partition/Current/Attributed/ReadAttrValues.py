from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.AttributedSlots import (
    KAttributedValueKinds,
)


# a registered attribute identity must have the observed bound value slot shapes
def ReadAttrValues(
    Nodes: Mapping[int, XmtNode], Attribute: XmtNode, Widths: tuple[int | None, ...]
) -> tuple[int, ...]:
    Definition = Nodes[Attribute.Integer("definition")]
    Result: list[int] = []
    for FieldCode, IndexValue, Width in zip(
        Definition.Indexes("fields"), Attribute.Indexes("fields"), Widths, strict=True
    ):
        if (Width == 0) != (IndexValue == 0):
            raise ValueError(
                "attributed active attribute has an unsupported value slot"
            )
        if not IndexValue:
            continue
        Value = RequireXmt(Nodes, IndexValue, KAttributedValueKinds[FieldCode])
        ValueData = Value.FieldsValue["values"]
        if not isinstance(ValueData, tuple):
            raise ValueError("attributed active attribute value is not a typed array")
        CountValue = len(CastValue(tuple[object, ...], ValueData))
        if (
            Definition.Indexes("fields") == (9, 9, 1, 1)
            and Width is None
            and CountValue not in (5, 6)
        ):
            raise ValueError("attributed active face producer has an unsupported width")
        if not CountValue or Width is not None and CountValue != Width:
            raise ValueError(
                "attributed active attribute value has an unsupported width"
            )
        Result.append(IndexValue)
    return tuple(Result)
