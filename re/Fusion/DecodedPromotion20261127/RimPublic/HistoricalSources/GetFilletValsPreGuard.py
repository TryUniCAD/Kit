from sys import float_info as FloatInfo
from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# geometry must evaluate the exact owned controls without substituting stale definition values
def GetFilletVals(
    StepValue: FeatureStep,
    Definition: RadiusFillet,
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[float, float]:
    if StepValue.kind != FeatureKind.KFillet:
        raise ValueError("radius fillet requires a fillet feature")
    Selected = Selections.get(Definition.EdgeSelectionId)
    if (
        Definition.EdgeSelectionId not in StepValue.selection_ids
        or Selected is None
        or not (Selected.path or Selected.query)
    ):
        raise ValueError("radius fillet requires its resolved edge selection")
    Values: list[float] = []
    for Identity, KindValue, UnitName in (
        (Definition.RadiusParameterId, ValueKind.KLength, "mm"),
        (Definition.WeightParameterId, ValueKind.KNumber, ""),
    ):
        Param = Parameters.get(Identity)
        if (
            Param is None
            or Param.owner_id != StepValue.id
            or Identity not in StepValue.parameter_ids
        ):
            raise ValueError(
                f"radius fillet has an unlinked or unowned control {Identity}"
            )
        Number = Param.value.value
        if (
            Param.value.kind != KindValue
            or Param.value.unit != UnitName
            or not isinstance(Number, (float, int))
            or isinstance(Number, bool)
            or not 0 < Number <= FloatInfo.max
        ):
            raise ValueError(
                "radius fillet controls require finite positive mm and unitless values"
            )
        Values.append(Number)
    if (
        Values[1] != 1.0
        or not Definition.TangentChain
        or not Definition.RollingBallCorners
    ):
        raise ValueError(
            "radius fillet requires unit tangency and rolling ball chain mode"
        )
    return Values[0], Values[1]
