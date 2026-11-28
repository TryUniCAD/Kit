from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevStep import (
    BindRevStep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.geometry.Models.Selection import Selection


# the decoded native step keeps its true sweep and all independent wall relationships
def BindThinStep(
    StepValue: FeatureStep,
    LinkValue: NativeLink,
    OwnerValue: ThinRevOwner,
    SelectValue: Selection,
    ParamIds: tuple[str, ...],
) -> FeatureStep:
    Projected = BindRevStep(StepValue, OwnerValue.SweepValue, LinkValue, SelectValue)
    AnglesValue = Projected.definition
    if not isinstance(AnglesValue, AngularRevolve):
        raise ValueError(
            "SOLIDWORKS thin revolve is missing its actual angular control"
        )
    return ReplaceValue(
        Projected,
        operation=BooleanOp.KCreate,
        parameter_ids=ParamIds,
        definition=ThinRevolve(
            AnglesValue,
            OwnerValue.ModeValue,
            ParamIds[1],
            ParamIds[2] if len(ParamIds) == 3 else None,
        ),
    )
