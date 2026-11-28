from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)


# an owned child preserves an independent verified environment order and the actual creation events
def CheckCylLights(
    PlanValue: CirclePlan,
    RecipeValue: PartBuildInput,
    LightValues: tuple[LightInput, ...],
) -> None:
    if type(CastValue(object, LightValues)) is not tuple or any(
        type(ValueInput) is not LightInput for ValueInput in LightValues
    ):
        raise TypeError("concentric attachment requires ordered typed light intents")
    TypesValue = tuple(ValueInput.KindValue for ValueInput in LightValues)
    if TypesValue not in (
        ("ambient",),
        ("ambient", "directional", "directional", "directional"),
    ):
        raise ValueError(
            "concentric attachment requires the measured ambient or ordered four-light scene"
        )
    WrittenAt = RecipeValue.OutputValue.SavedAt
    ClockValues = tuple(
        ValueInput.CreatedValue.FractionTicks for ValueInput in LightValues
    )
    if any(
        ValueInput.CreatedValue.SecondsValue != WrittenAt for ValueInput in LightValues
    ) or any(
        LeftValue >= RightValue
        for LeftValue, RightValue in zip(ClockValues, ClockValues[1:])
    ):
        raise ValueError(
            "concentric child light times must follow the modeled generation event"
        )
    NamesValue = (
        *(
            Value
            for _, Value in (
                *RecipeValue.SystemValue.FolderValues,
                *RecipeValue.SystemValue.PlaneNames,
            )
        ),
        RecipeValue.SystemValue.CabinetName,
        RecipeValue.SystemValue.OriginName,
        PlanValue.FeatureName,
        PlanValue.SketchName,
        *(ValueInput.NameValue for ValueInput in LightValues),
    )
    if len({Value.casefold() for Value in NamesValue}) != len(NamesValue):
        raise ValueError("concentric attachment requires unique owned scene names")
