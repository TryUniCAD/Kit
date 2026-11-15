from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureExtrude import ExtrudeFeature

KCreatorCases = (
    "NoDependency",
    "EmptyProfile",
    "UnknownProfile",
    "ConstructionProfile",
    "SuppressedSketch",
    "LegacyCreator",
)


def BuildCreator(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(DocumentSpec("Creator prerequisites", "height", 20.0))
    Sketch = Document.sketches[0]
    Feature = Document.feature_timeline[-1]
    if RecordKind == "NoDependency":
        Feature = ReplaceData(Feature, input_feature_ids=())
    elif RecordKind == "EmptyProfile":
        Sketch = ReplaceData(Sketch, closed_profile_entity_ids=())
    elif RecordKind == "UnknownProfile":
        Sketch = ReplaceData(Sketch, closed_profile_entity_ids=(("missing",),))
    elif RecordKind == "ConstructionProfile":
        Sketch = ReplaceData(
            Sketch,
            entities=tuple(
                ReplaceData(Entity, construction=True) for Entity in Sketch.entities
            ),
        )
    elif RecordKind == "SuppressedSketch":
        Sketch = ReplaceData(Sketch, suppressed=True)
    else:
        Feature = ReplaceData(
            Feature, definition=ExtrudeFeature(Document.parameters[0].value)
        )
    return ReplaceData(
        Document,
        metadata={},
        sketches=(Sketch,),
        feature_timeline=(*Document.feature_timeline[:-1], Feature),
    )
