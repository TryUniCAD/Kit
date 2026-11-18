from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileList import (
    NeedProfileList,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileSet import (
    ProfileSet,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadProfileItem import (
    ReadProfileItem,
)


# only actual view owned profile collections can extend the empty annotation folder profile
def ReadProfileSet(FolderValue: ArchiveNode, VersionValue: int) -> ProfileSet:
    if VersionValue != 19000:
        raise BodyUnsupported("drawing profile display requires archive version 19000")
    _ = NeedProfileNode(FolderValue, "moDetailFolder_c")
    RowsValue = NeedProfileList(FolderValue.FieldsValue.get("f8f8"))
    if not RowsValue:
        return ProfileSet(FolderValue, ())
    ViewValue = NeedProfileNode(FolderValue.FieldsValue.get("owner"), "moAbsoluteView")
    if ViewValue.FieldsValue.get("f630") is not FolderValue:
        raise BodyUnsupported("drawing profile display has a foreign owning view")
    ItemsValue = tuple(
        ReadProfileItem(Value, FolderValue, ViewValue) for Value in RowsValue
    )
    if len({Value.DisplayValue for Value in ItemsValue}) != len(ItemsValue):
        raise BodyUnsupported(
            "drawing profile display contains duplicate display objects"
        )
    return ProfileSet(FolderValue, ItemsValue)
