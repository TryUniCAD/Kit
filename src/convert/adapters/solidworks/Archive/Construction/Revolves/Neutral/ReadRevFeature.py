from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve


# a fresh angular boss must use its actual sole positive radian driver and preserve the selected end ownership
def ReadRevFeature(DocumentValue: CadDocument) -> tuple[AngularRevolve, float]:
    FeatureValue = DocumentValue.feature_timeline[0]
    DefinitionValue = FeatureValue.definition
    Parameter = DocumentValue.parameters[0]
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
    if (
        DefinitionValue.SideMode != "one_sided"
        or DefinitionValue.AgainstParameterId is not None
        or Parameter.name != "D1"
        or Parameter.role != ParameterRole.KDriving
        or Parameter.owner_id != FeatureValue.id
        or Parameter.expression is not None
        or Parameter.attributes
        or Parameter.value.kind != ValueKind.KAngle
        or Parameter.value.unit != "rad"
        or DefinitionValue.AlongParameterId != Parameter.id
        or FeatureValue.parameter_ids != (Parameter.id,)
    ):
        raise ValueError(
            "revolve construction requires its actual sole D1 radian driver"
        )
    AngleValue = ReadStyleNum(Parameter.value.value, "revolve angle")
    if not 1e-8 < AngleValue <= FullTurn:
        raise ValueError("revolve angle must be positive through one full turn")
    return DefinitionValue, AngleValue
