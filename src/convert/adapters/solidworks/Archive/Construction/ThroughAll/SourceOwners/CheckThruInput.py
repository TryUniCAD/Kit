from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)


# a component constructor must reject lost source parents unknown scope or mismatched target datum and unit choices before allocation
def CheckThruInput(InputValue: ThruOwnerInput, SettingsValue: PartBuildInput) -> None:
    if (
        type(InputValue) is not ThruOwnerInput
        or type(SettingsValue) is not PartBuildInput
    ):
        raise TypeError(
            "through-all owners require typed byte-free input and explicit target settings"
        )
    Stock, RefsValue = InputValue.ShapeValue.StockValue, InputValue.RefsValue
    if (
        RefsValue.StockOperation != "join"
        or RefsValue.StockParents != (RefsValue.StockProfileId,)
        or RefsValue.CutParents != (Stock.FeatureId, RefsValue.CutProfileId)
    ):
        raise ValueError(
            "source owner input lost actual join or profile dependency semantics"
        )
    if (
        CastValue(object, InputValue.ScopeValue.ModeValue) != "selected"
        or InputValue.ScopeValue.VersionValue != 19000
        or InputValue.ScopeValue.StockValues != (Stock,)
        or InputValue.ScopeValue.StockValues[0] is not Stock
    ):
        raise ValueError("source owners require the actual explicit selected stock")
    Planes = {Value.AxisValue: Value.NameValue for Value in InputValue.PlaneValues}
    if (
        len(InputValue.PlaneValues) != 3
        or set(Planes) != {"x", "y", "z"}
        or dict(SettingsValue.SystemValue.PlaneNames) != Planes
    ):
        raise ValueError(
            "generated system does not preserve all actual source datum names"
        )
    if SettingsValue.DocumentUnits.LengthUnit != InputValue.UnitValue:
        raise ValueError("target document units differ from source owner units")
    if (
        len(InputValue.LineValues) != 4
        or any(type(Value.TargetIndex) is not int for Value in InputValue.LineValues)
        or {Value.TargetIndex for Value in InputValue.LineValues} != set(range(4))
    ):
        raise ValueError("source lines lack a complete fresh contour correspondence")
    if len(InputValue.AxisValues) != 2 or {
        Value.FeatureId for Value in InputValue.AxisValues
    } != {Stock.FeatureId, RefsValue.CutFeatureId}:
        raise ValueError("source sketch normal ownership is missing or ambiguous")
