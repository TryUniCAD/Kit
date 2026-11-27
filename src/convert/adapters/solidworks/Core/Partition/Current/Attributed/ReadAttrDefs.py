from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.AttributedSlots import (
    KAttributeOwnerSlots,
    KAttributedSlots,
)


# the active profile admits only registered definitions consistent with their native owners
def ReadAttrDefs(Nodes: Mapping[int, XmtNode], Indices: set[int]) -> dict[int, str]:
    Definitions: dict[int, str] = {}
    for IndexValue in Indices:
        Definition = Nodes[IndexValue]
        NameValue = RequireXmt(Nodes, Definition.Integer("identifier"), 79).String(
            "string"
        )
        if (
            NameValue not in KAttributedSlots
            or Definition.Indexes("fields") != KAttributedSlots[NameValue][1]
        ):
            raise ValueError(
                "attributed active definition is outside the witnessed profile"
            )
        OwnerKind = KAttributedSlots[NameValue][0]
        if Definition.Indexes("legal_owners")[KAttributeOwnerSlots[OwnerKind]] != 1:
            raise ValueError(
                "attributed active definition disallows its physical owner"
            )
        Definitions[IndexValue] = NameValue
    return Definitions
