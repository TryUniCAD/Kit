from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Profiles.CanHideProfile import (
    CanHideProfile,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileMap import (
    NeedProfileMap,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileDisplay import (
    ProfileDisplay,
)


# display owner aliases must identify the actual folder and view rather than matching identifiers
def ReadProfileItem(
    Value: object, FolderValue: ArchiveNode, ViewValue: ArchiveNode
) -> ProfileDisplay:
    RowFields = NeedProfileMap(Value)
    if set(RowFields) != {"o"}:
        raise BodyUnsupported("drawing profile display has unknown list row fields")
    DisplayValue = NeedProfileNode(RowFields.get("o"), "moDisplayProfileFeature_c")
    FieldsValue = DisplayValue.FieldsValue
    ReferenceValue = NeedProfileNode(FieldsValue.get("f48"), "moCompProfile_c")
    if (
        FieldsValue.get("f30") is not FolderValue
        or FieldsValue.get("f40") is not ViewValue
    ):
        raise BodyUnsupported(
            "drawing profile display has foreign folder or view aliases"
        )
    CanHideValue = CanHideProfile(FieldsValue)
    return ProfileDisplay(
        DisplayValue, FolderValue, ViewValue, ReferenceValue, CanHideValue
    )
