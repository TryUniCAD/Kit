from collections.abc import Callable, Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# class and virtual predicates must use the concrete typed receiver and proven dispatch map
def ExprSpecial(
    FrameValue: ExprFrame,
    ActionValue: str,
    Arguments: tuple[object, ...],
    ReadValue: Callable[[tuple[object, ...]], object],
) -> object:
    Values = tuple(
        ReadValue(CastValue(tuple[object, ...], Expression)) for Expression in Arguments
    )
    if ActionValue == "is_node":
        return isinstance(Values[0], ArchiveNode)
    if ActionValue == "class_of":
        return ArchiveNode.RequireNode(Values[0]).ClassValue.NameValue
    if ActionValue == "virtual":
        RuleValue = NativeField("Virtual", "", MaskValue=CastValue(int, Values[0]))
        return GetVirtualRule(
            FrameValue.ContextValue, ArchiveNode.RequireNode(Values[1]), RuleValue
        )
    if ActionValue == "sum_field":
        RowsValue = CastValue(Sequence[Mapping[str, int]], Values[0])
        return sum(RowValue[CastValue(str, Values[1])] for RowValue in RowsValue)
    raise ValueError(f"unsupported native symbolic operation {ActionValue}")
