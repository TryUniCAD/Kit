from convert.adapters.freecad.BodyLineage.BoxNativeOwner import CheckBoxPlace
from convert.adapters.freecad.BodyLineage.CheckBoxParams import CheckBoxParams
from convert.adapters.freecad.Native import ElemData, NativeObject
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter

# only the observed independent legacy stock properties are modeled in this recipe
KStockProps = frozenset(
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


# fixed principal stock needs its actual unlinked and unrotated source placement
def CheckStockPlace(OwnerValue: NativeObject, FeatureName: str) -> None:
    CheckBoxPlace(OwnerValue, "Placement")
    CheckBoxPlace(OwnerValue, "AttachmentOffset")
    Properties = {
        KeyValue: ElemData(Value) for KeyValue, Value in OwnerValue.properties.items()
    }
    if Properties.keys() != KStockProps:
        raise ValueError("FreeCAD stock has unrepresented primitive properties")
    for NameValue, KindValue, TagValue, Expected in (
        ("AttacherType", "String", "String", "Attacher::AttachEngine3D"),
        ("Label", "String", "String", FeatureName),
        ("Label2", "String", "String", ""),
        ("MapMode", "Enumeration", "Integer", "0"),
        ("MapReversed", "Bool", "Bool", "false"),
    ):
        RequireProp(Properties, NameValue, KindValue, TagValue, Expected)
    RequireEmpty(Properties, "Support", "LinkSubList", "LinkSubList")
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


# primitive dimensions retain the actual stored parameter ids aliases and independent values
def ReadStockDims(
    Parameters: tuple[Parameter, ...],
    OwnerValue: NativeObject,
    FeatureValue: FeatureStep,
) -> tuple[Parameter, Parameter, Parameter]:
    Owned = tuple(Value for Value in Parameters if Value.owner_id == FeatureValue.id)
    CheckBoxParams(Owned, OwnerValue, FeatureValue)
    CheckStockPlace(OwnerValue, FeatureValue.name)
    Lookup = {Value.attributes.get("freecad_path"): Value for Value in Owned}
    Length, Width, Height = (
        Lookup[KeyValue] for KeyValue in ("Length", "Width", "Height")
    )
    for Value in (Length, Width, Height):
        if (
            Value.value.unit != "mm"
            or Value.expression is not None
            or ReadLength(Value.value) <= 0
        ):
            raise ValueError(
                "FreeCAD stock requires three positive independent lengths"
            )
    return Length, Width, Height
