from collections.abc import Mapping
from math import isfinite

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KDimensions,
    KFeatureScalars,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# every scalar must have its own neutral driver with the exact source property and primitive owner
def ReadParamOwners(
    Parameters: tuple[Parameter, ...],
    Feature: FeatureStep,
    Properties: Mapping[str, object],
    Release: str,
) -> dict[str, Parameter]:
    Scalars: dict[str, Parameter] = {}
    for ParameterValue in Parameters:
        PathValue = ParameterValue.attributes.get("freecad_path")
        if (
            not isinstance(PathValue, str)
            or PathValue in Scalars
            or ParameterValue.owner_id != Feature.id
            or ParameterValue.expression is not None
        ):
            raise ValueError(
                "FreeCAD primitive contains a foreign, duplicate or expressed parameter"
            )
        SourceProp = NativeRecord(Properties[PathValue])
        RequireBox(
            ParameterValue.attributes.get("freecad_property") == SourceProp
            and ParameterValue.attributes.get("freecad_property_type")
            == NativeRecord(SourceProp["attributes"])["type"],
            "FreeCAD neutral driver lost its actual source property",
        )
        Scalars[PathValue] = ParameterValue
    Expected = KFeatureScalars
    if Release != "0.21":
        Expected |= {"AttacherEngine", "Suppressed"}
    if Release == "1.1":
        Expected |= {"FuzzyTolerance"}
    RequireBox(
        frozenset(Scalars) == Expected
        and {ItemValue.id for ItemValue in Parameters} == set(Feature.parameter_ids),
        "FreeCAD box contains a foreign driving property",
    )
    return Scalars


# the neutral attachment and suppression owners must agree with their preserved literals
def CheckBoxScalars(
    Scalars: Mapping[str, Parameter],
    Properties: Mapping[str, object],
    Release: str,
) -> None:
    if Release != "0.21":
        RequireBox(
            Scalars["AttacherEngine"].value.value == "Engine 3D"
            and Scalars["Suppressed"].value.value is False
            and Scalars["Refine"].value.value
            == (ReadPropText(Properties, "Refine", "Bool", "Bool") == "true"),
            "FreeCAD box carries an inconsistent attachment, refinement or suppression owner",
        )
    if Release == "1.1":
        RequireBox(
            Scalars["FuzzyTolerance"].value.value == -1.0,
            "FreeCAD box carries an inconsistent neutral tolerance owner",
        )


# the source dimensions define three positive independent length drivers in millimetres
def ReadBoxParams(
    Parameters: tuple[Parameter, ...],
    Feature: FeatureStep,
    Properties: Mapping[str, object],
    Release: str,
) -> tuple[tuple[Parameter, Parameter, Parameter], tuple[float, float, float]]:
    Scalars = ReadParamOwners(Parameters, Feature, Properties, Release)
    CheckBoxScalars(Scalars, Properties, Release)
    Length, Width, Height = (
        float(ReadPropText(Properties, NameValue, "Length", "Float"))
        for NameValue in KDimensions
    )
    Owners = (Scalars["Length"], Scalars["Width"], Scalars["Height"])
    Measures = (Length, Width, Height)
    RequireBox(
        all(
            isfinite(SizeValue)
            and SizeValue > 0.0
            and Driver.value.value == SizeValue
            and Driver.value.unit == "mm"
            and str(Driver.value.kind) == "length"
            and str(Driver.role) == "driving"
            for Driver, SizeValue in zip(Owners, Measures, strict=True)
        ),
        "FreeCAD box does not carry three positive independent source dimensions",
    )
    return Owners, Measures
