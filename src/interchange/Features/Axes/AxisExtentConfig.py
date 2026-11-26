from collections.abc import Mapping
from dataclasses import dataclass as DataClass, replace as ReplaceValue

from interchange.Features.Axes.AxisConfigChain import GetAxisConfigs
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue


# each document validation needs one index for all bound axes in the selected configuration
@DataClass(frozen=True, slots=True)
class AxisConfigView:
    ConfigIds: frozenset[str]
    SuppressedIds: frozenset[str]
    ExtentValues: Mapping[str, ParameterValue | None]
    ErrorText: str | None = None


# nearest overrides replace ancestor results without scanning configuration entries for every axis
def MakeAxisView(Configurations: tuple[Configuration, ...]) -> AxisConfigView:
    try:
        Chain = GetAxisConfigs(Configurations)
    except ValueError as ErrorInfo:
        return AxisConfigView(frozenset(), frozenset(), {}, str(ErrorInfo))
    ExtentValues: dict[str, ParameterValue | None] = {}
    for Config in reversed(Chain):
        Current: dict[str, ParameterValue | None] = {}
        for Entry in Config.overrides:
            Identity = Entry.parameter_id
            Current[Identity] = None if Identity in Current else Entry.value
        ExtentValues.update(Current)
    return AxisConfigView(
        frozenset(Config.id for Config in Chain),
        frozenset(
            Identity for Config in Chain for Identity in Config.suppressed_feature_ids
        ),
        ExtentValues,
    )


# variant data replaces the extent value while leaving its actual parameter owner intact
def ConfigAxisParam(Param: Parameter, ViewValue: AxisConfigView) -> Parameter:
    Effective = ViewValue.ExtentValues.get(Param.id, Param.value)
    if Effective is None:
        raise ValueError(f"has ambiguous configured extent {Param.id}")
    return Param if Effective is Param.value else ReplaceValue(Param, value=Effective)


# suppression retains the editable definition without contributing a resolved segment
def IsSuppressed(StepValue: FeatureStep, ViewValue: AxisConfigView) -> bool:
    return (
        StepValue.suppressed
        or StepValue.id in ViewValue.SuppressedIds
        or any(
            State.suppressed and State.configuration_id in ViewValue.ConfigIds
            for State in StepValue.configuration_states
        )
    )
