from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a valid reference to another mapped object would still misidentify the embedded map
def CheckBlockOwner(RootValue: ArchiveNode, *, RequireEmpty: bool = True) -> None:
    FieldsValue = CastValue(dict[str, object], RootValue.FieldsValue["blocks"])
    if FieldsValue["f30"] is not RootValue:
        raise BodyUnsupported(
            "SOLIDWORKS sketch block map requires its owning backlink"
        )
    if RequireEmpty and (FieldsValue["n70"] != 0 or FieldsValue["n98"] != 0):
        raise BodyUnsupported("populated SOLIDWORKS sketch block maps are unqualified")
