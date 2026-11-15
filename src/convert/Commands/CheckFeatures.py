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
    ActiveFeatures = set[str]()
    SuppressedFeatures = {
        FeatureId
        for Configuration in Document.configurations
        for FeatureId in Configuration.suppressed_feature_ids
    }
    for Feature in sorted(Document.feature_timeline, key=lambda Value: Value.order):
        if Feature.kind not in KPortableKinds:
            raise ValueError(KFeatureError)
        if Feature.kind == FeatureKind.KReference:
            if Feature.definition is None and not Feature.sketch_id:
                raise ValueError(KFeatureError)
        elif Feature.definition is None:
            raise ValueError(KFeatureError)
        if (
            Feature.suppressed
            or Feature.id in SuppressedFeatures
            or any(State.suppressed for State in Feature.configuration_states)
            or any(
                InputId not in ActiveFeatures for InputId in Feature.input_feature_ids
            )
        ):
            continue
        ActiveFeatures.add(Feature.id)
        if Feature.kind != FeatureKind.KReference:
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
