from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ThinWallPlan import (
    ThinWallPlan,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.ThinRevValidate import GetRevWall
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ThinRevolve import ThinRevolve

# native direction words follow the registered thin wall enum
KThinModeWords = {"one_sided": 0, "opposite": 1, "midplane": 2, "two_sided": 3}


# each physical display belongs to its own declared driver within the measured annular domain
def ReadThinWall(
    DocumentValue: CadDocument,
    FeatureValue: FeatureStep,
    Definition: ThinRevolve,
    RadiusValue: float,
) -> ThinWallPlan:
    DriverIds = Definition.GetWallIds()
    ParameterValues = {Value.id: Value for Value in DocumentValue.parameters}
    NamesValue = ("D3", "D4")[: len(DriverIds)]
    LengthsValue: list[float] = []
    for ParameterId, NameValue in zip(DriverIds, NamesValue, strict=True):
        LengthValue = GetRevWall(FeatureValue, ParameterId, ParameterValues) * 0.001
        Parameter = ParameterValues[ParameterId]
        if (
            not 0.0 < LengthValue < RadiusValue
            or Parameter.name != NameValue
            or Parameter.expression is not None
            or Parameter.attributes
        ):
            raise ValueError(
                "thin wall must be a plain editable driver clear of the axis"
            )
        LengthsValue.append(LengthValue)
    FirstValue, SecondValue = (LengthsValue + [0.0])[:2]
    if FirstValue == SecondValue:
        raise ValueError("two-sided thin revolve requires two unequal wall lengths")
    return ThinWallPlan(KThinModeWords[Definition.WallMode], (FirstValue, SecondValue))
