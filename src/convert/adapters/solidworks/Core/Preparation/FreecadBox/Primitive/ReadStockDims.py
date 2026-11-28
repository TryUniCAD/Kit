from convert.adapters.freecad.BodyLineage.CheckBoxParams import CheckBoxParams
from convert.adapters.freecad.Native import NativeObject
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# primitive dimensions retain the actual stored parameter ids aliases and independent values
def ReadStockDims(
    Parameters: tuple[Parameter, ...],
    OwnerValue: NativeObject,
    FeatureValue: FeatureStep,
) -> tuple[Parameter, Parameter, Parameter]:
    Owned = tuple(Value for Value in Parameters if Value.owner_id == FeatureValue.id)
    CheckBoxParams(Owned, OwnerValue, FeatureValue)
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
