from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Partition.Current.Attributed.AttributedShapes import (
    KAttributedShapes,
    KAttributedTargets,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# every field used for reachability must resolve to its admitted native target domain
def AttributedRefs(Nodes: Mapping[int, XmtNode], NodeValue: XmtNode) -> tuple[int, ...]:
    References: list[int] = []
    for Field in KAttributedShapes[NodeValue.KindValue].FieldsValue:
        if Field.EncodingValue == "p":
            Targets = (
                NodeValue.Indexes(Field.NameValue)
                if Field.CountValue
                else (NodeValue.Integer(Field.NameValue),)
            )
            Admitted = KAttributedTargets.get(
                Field.PointerClass, frozenset((Field.PointerClass,))
            )
            for IndexValue in Targets:
                if not IndexValue:
                    continue
                if (
                    IndexValue not in Nodes
                    or Nodes[IndexValue].KindValue not in Admitted
                ):
                    raise ValueError("unqualified attributed active pointer target")
                References.append(IndexValue)
        elif Field.EncodingValue in ("f", "v"):
            Value = NodeValue.FieldsValue[Field.NameValue]
            Members = Value if isinstance(Value, tuple) else (Value,)
            if any(
                type(Member) is not float or not IsFinite(Member) for Member in Members
            ):
                raise ValueError("attributed active record has nonfinite geometry")
    return tuple(References)
