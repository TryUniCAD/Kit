from dataclasses import replace as ReplaceValue

from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter


# variant data replaces the extent value while leaving its actual parameter owner intact
def ConfigAxisParam(Param: Parameter, Chain: tuple[Configuration, ...]) -> Parameter:
    for Config in Chain:
        Overrides = tuple(
            Entry for Entry in Config.overrides if Entry.parameter_id == Param.id
        )
        if len(Overrides) > 1:
            raise ValueError(f"has ambiguous configured extent {Param.id}")
        if Overrides:
            return ReplaceValue(Param, value=Overrides[0].value)
    return Param


# suppression retains the editable definition without contributing a resolved segment
def IsSuppressed(StepValue: FeatureStep, Chain: tuple[Configuration, ...]) -> bool:
    ConfigIds = {Config.id for Config in Chain}
    return (
        StepValue.suppressed
        or any(StepValue.id in Config.suppressed_feature_ids for Config in Chain)
        or any(
            State.suppressed and State.configuration_id in ConfigIds
            for State in StepValue.configuration_states
        )
    )
