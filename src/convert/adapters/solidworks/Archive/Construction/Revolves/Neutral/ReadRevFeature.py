from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevDriver import (
    ReadRevDriver,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.RevolveSpan import GetAngleSpan


# angular boss construction needs each actual editable driver before native end objects can be allocated
def ReadRevFeature(
    DocumentValue: CadDocument,
) -> tuple[AngularRevolve, float, float | None]:
    FeatureValue = DocumentValue.feature_timeline[0]
    DefinitionValue = FeatureValue.definition
    if (
        FeatureValue.kind != FeatureKind.KRevolution
        or FeatureValue.operation not in (BooleanOp.KCreate, BooleanOp.KJoin)
        or type(DefinitionValue) is not AngularRevolve
        or FeatureValue.order != 0
        or FeatureValue.input_feature_ids
        or FeatureValue.suppressed
        or FeatureValue.configuration_states
        or FeatureValue.attributes
    ):
        raise ValueError("revolve construction requires one ordinary angular boss")
    ModeValue = DefinitionValue.SideMode
    if ModeValue not in ("one_sided", "symmetric_full", "two_sided"):
        raise ValueError("revolve construction requires a native angular end mode")
    Along = DefinitionValue.AlongParameterId
    Against = DefinitionValue.AgainstParameterId
    DriverIds = (Along,) if Against is None else (Along, Against)
    Parameters = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    if FeatureValue.parameter_ids != DriverIds or Parameters.keys() != set(DriverIds):
        raise ValueError("revolve construction requires all actual angular drivers")
    AngleValue = ReadRevDriver(Parameters[Along], FeatureValue.id, "D1")
    AgainstValue = (
        None
        if Against is None
        else ReadRevDriver(Parameters[Against], FeatureValue.id, "D2")
    )
    Start, End = GetAngleSpan(AngleValue, AgainstValue, ModeValue)
    if End - Start > FullTurn:
        raise ValueError("revolve angle must be positive through one full turn")
    if ModeValue != "one_sided" and End - Start == FullTurn:
        raise ValueError("multiple revolve ends require a partial angular sweep")
    return DefinitionValue, AngleValue, AgainstValue
