from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# shared identity checks keep external records within their measured ordinary archive profile
def CheckExtFields(FieldsValue: Mapping[str, object]) -> None:
    Owner = FieldsValue.get("f10")
    NameNode = FieldsValue.get("f38")
    if not isinstance(Owner, Mapping):
        raise BodyUnsupported("unsupported native external feature file identity owner")
    OwnerFields = CastValue(Mapping[str, object], Owner)
    if (OwnerFields.get("f20"), OwnerFields.get("f08")) != (3, 0):
        raise BodyUnsupported("unsupported native external feature file identity mode")
    if not isinstance(NameNode, ArchiveNode) or NameNode.ClassValue != RuntimeClass(
        "moCStringHandle_c", 1
    ):
        raise BodyUnsupported("unsupported native external feature name owner")
    if (
        FieldsValue.get("f40") != 0
        or FieldsValue.get("f58") != -1
        or FieldsValue.get("f18") != {"f08": "", "f10": -1}
        or "f50" not in FieldsValue
    ):
        raise BodyUnsupported("unsupported native external feature reference profile")
