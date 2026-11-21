from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# the first blind boss in the history derives its profile bounds and portable identities
def MakeBlindPlan(
    DocumentValue: CadDocument,
    VerticesValue: tuple[tuple[float, float], ...],
    ParameterId: str,
    DepthValue: float,
    DepthName: str,
    *,
    AxisValue: str = "z",
    IsReversed: bool = False,
) -> BlindPlan:
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    if not NameValue:
        raise ValueError("plain boss requires an explicit neutral document name")
    SketchValue = DocumentValue.sketches[0]
    FeatureValue = DocumentValue.feature_timeline[0]
    XValues, YValues = zip(*VerticesValue, strict=True)
    return BlindPlan(
        NameValue,
        DocumentValue.configurations[0].name,
        DocumentValue.support_planes[0].name,
        SketchValue.id,
        SketchValue.name,
        FeatureValue.id,
        FeatureValue.name,
        ParameterId,
        DocumentValue.bodies[0].id,
        VerticesValue,
        DepthValue,
        max(XValues) - min(XValues),
        max(YValues) - min(YValues),
        DepthName=DepthName,
        PrincipalAxis=AxisValue,
        Reversed=IsReversed,
    )
