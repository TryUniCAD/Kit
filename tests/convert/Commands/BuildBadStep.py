from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from tests.interchange.fixtures.DocumentFixture import BuildDocument

KBadKinds = {
    "GenericStep": FeatureKind.KExtrusion,
    "EmptyDefinition": FeatureKind.KExtrusion,
    "NativeKind": FeatureKind.KNative,
    "NativeDefined": FeatureKind.KNative,
    "UnknownKind": "fixture.unknown",
    "UnknownDefined": "fixture.unknown",
    "BareReference": FeatureKind.KReference,
    "BodyReference": FeatureKind.KReference,
}


def BuildBadStep(RecordKind: str) -> CadDocument:
    if RecordKind == "GenericStep":
        return BuildDocument()
    Document = MakeFusionDoc(DocumentSpec("Incomplete feature", "height", 20.0))
    Feature = Document.feature_timeline[-1]
    Feature = ReplaceData(
        Feature,
        kind=KBadKinds[RecordKind],
        definition=(
            Feature.definition
            if RecordKind in ("UnknownDefined", "NativeDefined")
            else None
        ),
        sketch_id=None if RecordKind == "BareReference" else Feature.sketch_id,
    )
    return ReplaceData(
        Document,
        feature_timeline=(*Document.feature_timeline[:-1], Feature),
        metadata={},
    )
