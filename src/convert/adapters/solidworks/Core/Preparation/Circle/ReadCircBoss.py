from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircDrive import (
    ReadCircDrive,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# both active physical ends retain their own live parameter and direction
def ReadCircBoss(
    StepValue: FeatureStep, Drivers: tuple[Parameter, ...]
) -> tuple[FeatureStep, tuple[Parameter, ...]]:
    Definition = StepValue.definition
    if type(Definition) is not ExtrudeFeature or StepValue.operation not in (
        BooleanOp.KCreate,
        BooleanOp.KJoin,
    ):
        raise ValueError("SOLIDWORKS circle readback lacks its actual ordinary boss")
    Lengths = (
        (Definition.length,)
        if Definition.second_length is None
        else (Definition.length, Definition.second_length)
    )
    if tuple(Value.value for Value in Drivers) != Lengths:
        raise ValueError("SOLIDWORKS circle readback end and driver values disagree")
    Converted = tuple(
        ReadCircDrive(Driver, StepValue.id, f"D{Index}")
        for Index, Driver in enumerate(Drivers, 1)
    )
    return (
        ReplaceValue(
            StepValue,
            order=0,
            operation=BooleanOp.KCreate,
            definition=ReplaceValue(
                Definition,
                length=Converted[0].value,
                second_length=Converted[1].value if len(Converted) == 2 else None,
            ),
            input_feature_ids=(),
            selection_ids=(),
            attributes=FreezeMapping(),
            provenance=None,
        ),
        Converted,
    )
