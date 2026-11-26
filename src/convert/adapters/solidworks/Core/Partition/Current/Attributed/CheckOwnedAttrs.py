from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Archive.Partition.ReadAttrHeads import ReadAttrHeads
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.AttributedSlots import (
    KAttributedSlots,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadAttrDefs import (
    ReadAttrDefs,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadAttrValues import (
    ReadAttrValues,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)


# every stored attribute and populated value must be accounted for before projection
def CheckOwnedAttrs(
    Nodes: Mapping[int, XmtNode], BodyValue: XmtNode, Kinds: Mapping[int, set[int]]
) -> dict[str, int]:
    CheckXmtAttrs(Nodes, BodyValue)
    Definitions = ReadAttrDefs(Nodes, Kinds.get(80, set()))
    Heads = ReadAttrHeads(Nodes, tuple(Definitions))
    if Heads.keys() != Definitions.keys():
        raise ValueError("attributed active attribute definition has no owner")
    Owned: set[int] = set()
    Values: set[int] = set()
    for NodeValue in Nodes.values():
        if "attributes_features" not in NodeValue.FieldsValue or not NodeValue.Integer(
            "attributes_features"
        ):
            continue
        for NameValue, Attribute in ReadBodyAttrs(Nodes, NodeValue).items():
            OwnerKind, _, Widths = KAttributedSlots[NameValue]
            Result = ReadAttrValues(Nodes, Attribute, Widths)
            if (
                OwnerKind != NodeValue.KindValue
                or Attribute.IndexValue in Owned
                or Values.intersection(Result)
                or len(Result) != len(set(Result))
            ):
                raise ValueError("attributed active attribute ownership is ambiguous")
            Owned.add(Attribute.IndexValue)
            Values.update(Result)
    if Owned != Kinds.get(81) or Values != set().union(
        *(Kinds.get(KindValue, set()) for KindValue in (82, 83, 98))
    ):
        raise ValueError("attributed active attribute inventory is incomplete")
    ByName = {
        Definitions[IndexValue]: HeadValue for IndexValue, HeadValue in Heads.items()
    }
    if "VERTEX_AUTOMATION_2_2001" not in ByName:
        raise ValueError("attributed active recovery requires owned vertex automation")
    return ByName
