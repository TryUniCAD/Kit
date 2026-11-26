from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KSketchBlockClass,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckBlockOwner import (
    CheckBlockOwner,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# populated references need owners outside this bounded manager reader
def CheckCfgOwner(RootValue: ArchiveNode) -> None:
    FieldsValue = RootValue.FieldsValue
    ResolvedValue = CastValue(dict[str, object], FieldsValue["f60"])
    ListValue = CastValue(dict[str, object], ResolvedValue["list"])
    if (
        FieldsValue["has_list68"] != 0
        or FieldsValue["has_f1e8"] != 0
        or ListValue["n"] != 0
        or any(
            FieldsValue[FieldName] is not None
            for FieldName in ("f18", "f78", "f258", "f2f0")
        )
    ):
        raise BodyUnsupported(
            "populated SOLIDWORKS feature owner fields are unqualified"
        )
    if RootValue.ClassValue == KSketchBlockClass:
        CheckBlockOwner(RootValue)
        return
    WordMapValue = CastValue(dict[str, object], FieldsValue["f368"])
    if (
        FieldsValue["f358"] is not None
        or FieldsValue["f360"] is not None
        or WordMapValue["n"] != 0
    ):
        raise BodyUnsupported(
            "populated SOLIDWORKS exploded view owners are unqualified"
        )
