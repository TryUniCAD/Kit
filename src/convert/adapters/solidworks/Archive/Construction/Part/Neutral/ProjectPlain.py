from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
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


# the supported neutral graph must project through actual semantic references before any native field graph or output byte is constructed
def ProjectPlain(DocumentValue: CadDocument) -> BlindPlan:
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
    VerticesValue = ReadRectSketch(SketchValue, ScaleValue)
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
