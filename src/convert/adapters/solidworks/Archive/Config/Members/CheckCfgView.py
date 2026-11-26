from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# populated presentation owners and extended transforms need separate native qualification
def CheckCfgView(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if any(Fields[NameValue] != 0 for NameValue in ("n380", "n398", "n3b0")):
        raise BodyUnsupported("unqualified SOLIDWORKS view lists")
    for NameValue in ("f368", "f370"):
        Transform = CastValue(dict[str, object], Fields[NameValue])
        FlagsValue = CastValue(int, Transform["f78"])
        if FlagsValue & 0xF0:
            raise BodyUnsupported("unqualified SOLIDWORKS view transform selector")
