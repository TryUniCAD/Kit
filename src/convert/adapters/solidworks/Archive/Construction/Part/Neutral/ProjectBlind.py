from collections.abc import Callable

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    RequirePlainDoc,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch


# rectangle and polygon admission must share neutral parameter support configuration and body ownership checks
def ProjectBlind(
    DocumentValue: CadDocument,
    ReadSketch: Callable[[Sketch, float], tuple[tuple[float, float], ...]],
) -> BlindPlan:
    RequirePlainDoc(DocumentValue)
    Definition = RequireBossDef(DocumentValue.feature_timeline[0])
    CheckPlainLinks(DocumentValue, Definition)
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if ScaleValue is None:
        raise ValueError(
            "plain boss document units are outside the supported dimensional profile"
        )
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    if not NameValue:
        raise ValueError("plain boss requires an explicit neutral document name")
    SketchValue = DocumentValue.sketches[0]
    FeatureValue = DocumentValue.feature_timeline[0]
    VerticesValue = ReadSketch(SketchValue, ScaleValue)
    WidthValue = max(PointValue[0] for PointValue in VerticesValue) - min(
        PointValue[0] for PointValue in VerticesValue
    )
    HeightValue = max(PointValue[1] for PointValue in VerticesValue) - min(
        PointValue[1] for PointValue in VerticesValue
    )
    return BlindPlan(
        NameValue,
        DocumentValue.configurations[0].name,
        DocumentValue.support_planes[0].name,
        SketchValue.id,
        SketchValue.name,
        FeatureValue.id,
        FeatureValue.name,
        DocumentValue.parameters[0].id,
        DocumentValue.bodies[0].id,
        VerticesValue,
        ReadLength(Definition.length),
        WidthValue,
        HeightValue,
    )
