from collections.abc import Mapping

from convert.adapters.freecad.BodyLineage.BoxNativeOwner import CheckBoxPlace
from convert.adapters.freecad.Native import ElemData, NativeObject
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadAxisPlace import (
    ReadAxisFrame,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import (
    ReadBoxMat,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadEnumText import (
    ReadEnumText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from interchange.geometry.Models.Transform import KAxisX, KAxisY, KAxisZ, Transform

# the legacy and current primitive schemas own the same dimensions under distinct attachment properties
KOldStockProps = frozenset(
    (
        "AttacherType",
        "AttachmentOffset",
        "ExpressionEngine",
        "Height",
        "Label",
        "Label2",
        "Length",
        "MapMode",
        "MapPathParameter",
        "MapReversed",
        "Placement",
        "Shape",
        "Support",
        "Visibility",
        "Width",
    )
)

# the newer owner uses a separate attachment engine and a typed material reference
KNewStockProps = KOldStockProps - {"Support"} | {
    "AttachmentSupport",
    "AttacherEngine",
    "ShapeMaterial",
}


# independently placed stock must declare its actual empty support and attachment state
def CheckStockProps(
    Properties: Mapping[str, object], NameValue: str, Placed: bool
) -> None:
    NamesValue = frozenset(Properties)
    if NamesValue == KOldStockProps:
        Support = "Support"
    elif Placed and NamesValue == KNewStockProps:
        Support = "AttachmentSupport"
        if ReadEnumText(Properties, "AttacherEngine") != "Engine 3D":
            raise ValueError(
                "FreeCAD stock requires its actual rigid attachment engine"
            )
        _ = ReadBoxMat(Properties)
    else:
        raise ValueError("FreeCAD stock has unrepresented primitive properties")
    for FieldName, KindValue, TagValue, Expected in (
        ("AttacherType", "String", "String", "Attacher::AttachEngine3D"),
        ("Label", "String", "String", NameValue),
        ("Label2", "String", "String", ""),
        ("MapMode", "Enumeration", "Integer", "0"),
        ("MapReversed", "Bool", "Bool", "false"),
    ):
        RequireProp(Properties, FieldName, KindValue, TagValue, Expected)
    RequireEmpty(Properties, Support, "LinkSubList", "LinkSubList")
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    if float(
        ReadPropText(Properties, "MapPathParameter", "Float", "Float")
    ) != 0 or ReadPropText(Properties, "Visibility", "Bool", "Bool") not in (
        "false",
        "true",
    ):
        raise ValueError(
            "FreeCAD stock requires an unlinked literal placement and visibility"
        )


# the placed stock rule consumes the actual rigid frame and refuses unimplemented rotations
def ReadStockPlace(
    OwnerValue: NativeObject, NameValue: str, *, Placed: bool
) -> Transform:
    if not Placed:
        CheckBoxPlace(OwnerValue, "Placement")
    CheckBoxPlace(OwnerValue, "AttachmentOffset")
    Properties = {
        KeyValue: ElemData(Value) for KeyValue, Value in OwnerValue.properties.items()
    }
    CheckStockProps(Properties, NameValue, Placed)
    PoseValue = ReadAxisFrame(Properties)
    if (PoseValue.x_axis, PoseValue.y_axis, PoseValue.z_axis) != (
        KAxisX,
        KAxisY,
        KAxisZ,
    ):
        raise ValueError("FreeCAD stock has an unsupported rigid rotation")
    return PoseValue
