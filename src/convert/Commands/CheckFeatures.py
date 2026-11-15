from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind

KPortableKinds = frozenset(
    KindValue for KindValue in FeatureKind if KindValue is not FeatureKind.KNative
)
KFeatureError = (
    "IncompleteFeature records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


def CheckFeatures(Document: CadDocument) -> None:
    FinalFeatures = {BodyValue.final_feature_id for BodyValue in Document.bodies}
    HasGenerator = False
    for Feature in Document.feature_timeline:
        if Feature.kind not in KPortableKinds:
            raise ValueError(KFeatureError)
        if Feature.kind == FeatureKind.KReference:
            if Feature.id in FinalFeatures or (
                Feature.definition is None and not Feature.sketch_id
            ):
                raise ValueError(KFeatureError)
            continue
        if Feature.definition is None:
            raise ValueError(KFeatureError)
        HasGenerator = True
    if (
        Document.brep is not None or Document.meshes or Document.bodies
    ) and not HasGenerator:
        raise ValueError(KFeatureError)
