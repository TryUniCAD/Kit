from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from interchange.Enums.EnumValues import ParameterRole
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# a native driving dimension must preserve the actual neutral parameter sketch support configuration and body owners before synthesis
def CheckPlainLinks(
    DocumentValue: CadDocument, Definition: ExtrudeFeature, DepthName: str = "D1"
) -> None:
    PlaneValue = CheckPartLinks(DocumentValue)
    Parameter, FeatureValue = (
        DocumentValue.parameters[0],
        DocumentValue.feature_timeline[0],
    )
    if (
        Parameter.role != ParameterRole.KDriving
        or Parameter.expression is not None
        or Parameter.owner_id != FeatureValue.id
        or Parameter.name != DepthName
        or Parameter.attributes
    ):
        raise ValueError(
            f"plain boss requires its actual unexpressed driving {DepthName} parameter"
        )
    if (
        FeatureValue.parameter_ids != (Parameter.id,)
        or Parameter.value != Definition.length
    ):
        raise ValueError(
            "plain boss feature definition and driving parameter values disagree"
        )
    if ReadPrincAxis(PlaneValue.transform) != "z":
        raise ValueError(
            "plain boss support must be the canonical front plane at the model origin"
        )
