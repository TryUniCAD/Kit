from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadWideName import (
    ReadWideName,
)


# both naming paths need the actual kernel wide string definition and slot types
def ReadImplicit(
    NodesValue: Mapping[int, XmtNode], Attributes: Mapping[str, XmtNode]
) -> str:
    Implicit = Attributes["SWIMPLICITBODYNAME_ID_U"]
    Definition = RequireXmt(NodesValue, Implicit.Integer("definition"), 80)
    FieldsValue = Implicit.Indexes("fields")
    if (
        Definition.Indexes("fields") != (10, 10)
        or len(FieldsValue) != 2
        or FieldsValue[1]
    ):
        raise ValueError("native implicit name fields are unqualified")
    return ReadWideName(RequireXmt(NodesValue, FieldsValue[0], 98).Indexes("values"))
