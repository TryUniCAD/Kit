from math import pi as PiValue

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevDriver import (
    ReadRevDriver,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Revolves.ThinRevolve import ThinRevolve


# the measured thin feature uses one positive angular driver and independent thickness controls
def ReadThinAngle(
    DocumentValue: CadDocument, FeatureValue: FeatureStep, Definition: ThinRevolve
) -> float:
    SweepValue = Definition.SweepValue
    if (
        SweepValue.SideMode != "one_sided"
        or FeatureValue.kind != FeatureKind.KRevolution
        or FeatureValue.order != 0
        or FeatureValue.operation != BooleanOp.KCreate
        or FeatureValue.suppressed
        or FeatureValue.input_feature_ids
        or FeatureValue.configuration_states
        or FeatureValue.attributes
    ):
        raise ValueError("thin revolve requires one partial single-direction boss")
    AngleId = SweepValue.AlongParameterId
    DriverIds = (AngleId, *Definition.GetWallIds())
    Parameters = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    if FeatureValue.parameter_ids != DriverIds or Parameters.keys() != set(DriverIds):
        raise ValueError("thin revolve requires each actual angle and wall driver")
    AngleValue = ReadRevDriver(Parameters[AngleId], FeatureValue.id, "D1")
    if not 0.0 < AngleValue < PiValue:
        raise ValueError("thin revolve requires a positive angle below a half turn")
    return AngleValue
