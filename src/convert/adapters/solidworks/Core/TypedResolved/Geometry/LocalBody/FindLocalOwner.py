from convert.adapters.solidworks.Container.Format import (
    CANONICAL_PLANE_FEATURE_TYPE as KCanonicalPlane,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel

# reference scaffold classes can accompany an import without adding solid history
KLocalScaffold = frozenset(
    (
        "moCommentsFolder_c",
        "moFavoriteFolder_c",
        "moHistoryFolder_c",
        "moSelectionSetFolder_c",
        "moSensorFolder_c",
        "moDocsFolder_c",
        "moSurfaceBodyFolder_c",
        "moSolidBodyFolder_c",
        "moEnvFolder_c",
        "moInkMarkupFolder_c",
        "moEqnFolder_c",
        "moMaterialFolder_c",
        "moDetailCabinet_c",
        "moRefPlane_c",
        "moOriginProfileFeature_c",
    )
)


# the local import must own the solid after excluding the retained native scaffold
def FindLocalOwner(ModelValue: NativeModel) -> NativeFeature | None:
    if ModelValue.operations:
        return None
    ImportValue = None
    for FeatureValue in ModelValue.features:
        ScaffoldType = FeatureValue.kind
        if (
            ScaffoldType == KCanonicalPlane.title()
            and FeatureValue.xml_tag == "Feature"
            and FeatureValue.properties.get("Type") == "moRefPlane_c"
        ):
            ScaffoldType = "moRefPlane_c"
        if ScaffoldType in KLocalScaffold and FeatureValue.class_name in (
            "",
            ScaffoldType,
        ):
            continue
        if (
            ImportValue is not None
            or FeatureValue.kind != "Imported"
            or FeatureValue.xml_tag != "Feature"
            or FeatureValue.class_name != "moBaseBody_c"
            or FeatureValue.native_stream != KResolvedFeaturesStream
            or FeatureValue.native_offset is None
            or FeatureValue.object_id <= 0
        ):
            return None
        ImportValue = FeatureValue
    if ImportValue is None or not any(
        Record.object_id == ImportValue.object_id
        and Record.offset == ImportValue.native_offset
        and Record.name == ImportValue.name
        for Record in ModelValue.names
    ):
        return None
    return ImportValue
