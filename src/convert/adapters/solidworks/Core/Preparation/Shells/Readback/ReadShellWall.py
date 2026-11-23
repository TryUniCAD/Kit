from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureKinds import ShellFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the wall thickness retains the exact metre word from the linked independent owner
def ReadShellWall(
    StepValue: FeatureStep, DriverValue: Parameter
) -> tuple[FeatureStep, Parameter]:
    Definition = StepValue.definition
    Display = DriverValue.value.value
    Owner = NativeRecord(DriverValue.attributes.get("typed_archive_owner"))
    if (
        type(Definition) is not ShellFeature
        or StepValue.parameter_ids != (DriverValue.id,)
        or DriverValue.owner_id != StepValue.id
        or DriverValue.value != Definition.thickness
        or DriverValue.value.unit != "mm"
        or DriverValue.attributes.get("native_unit") != "m"
        or Owner.get("slot") != "f818"
        or type(Display) is not float
    ):
        raise ValueError("SOLIDWORKS shell compilation lacks its exact wall driver")
    Thickness = ReplaceValue(
        DriverValue.value,
        value=ExactMm(DriverValue.attributes.get("native_value"), Display),
    )
    return (
        ReplaceValue(
            StepValue,
            definition=ReplaceValue(Definition, thickness=Thickness),
            provenance=None,
            attributes=FreezeMapping(),
        ),
        ReplaceValue(
            DriverValue, value=Thickness, provenance=None, attributes=FreezeMapping()
        ),
    )
