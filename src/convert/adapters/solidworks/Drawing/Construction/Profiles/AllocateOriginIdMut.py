from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# display publication must advance the actual owning model counter rather than reuse persistent feature or archive identities
def AllocateOriginIdMut(ModelValue: ArchiveNode, DisplayValue: ArchiveNode) -> int:
    _ = NeedProfileNode(ModelValue, "moDrawing_c")
    _ = NeedProfileNode(DisplayValue, "moDisplayProfileFeature_c")
    ExistingValue = FieldInt(DisplayValue.FieldsValue, "f58")
    if ExistingValue >= 10:
        if ExistingValue >= 0x7FFFFFFF:
            raise ValueError(
                "origin display identity exceeds the qualified signed domain"
            )
        return ExistingValue
    NextValue = FieldInt(ModelValue.FieldsValue, "fd44")
    if ExistingValue != 0 or not 10 <= NextValue < 0x7FFFFFFF:
        raise ValueError(
            "origin display allocation requires fresh bounded constructor state"
        )
    ModelValue.FieldsValue["fd44"] = NextValue + 1
    DisplayValue.FieldsValue["f58"] = NextValue
    return NextValue
