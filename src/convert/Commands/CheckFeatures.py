from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind

KPortableKinds = frozenset(
    KindValue
    for KindValue in FeatureKind
    if KindValue not in (FeatureKind.KNative, FeatureKind.KImported)
)
KFeatureError = (
    "IncompleteFeature records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


def CheckFeatures(Document: CadDocument) -> None:
    Generators = set[str]()
    for Feature in Document.feature_timeline:
        if Feature.kind not in KPortableKinds:
            raise ValueError(KFeatureError)
        if Feature.kind == FeatureKind.KReference:
            if Feature.definition is None and not Feature.sketch_id:
                raise ValueError(KFeatureError)
            continue
        if Feature.definition is None:
            raise ValueError(KFeatureError)
        Generators.add(Feature.id)
    if Document.meshes or any(
        BodyValue.final_feature_id not in Generators for BodyValue in Document.bodies
    ):
        raise ValueError(KFeatureError)
    BodyIds = {BodyValue.id for BodyValue in Document.bodies}
    if Document.brep is not None and (
        not Document.brep.bodies
        or any(
            BodyValue.design_body_id not in BodyIds
            for BodyValue in Document.brep.bodies
        )
    ):
        raise ValueError(KFeatureError)
