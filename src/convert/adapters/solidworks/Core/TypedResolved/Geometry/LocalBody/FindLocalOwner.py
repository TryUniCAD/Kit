from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.HasLocalHelpers import (
    HasLocalHelpers,
)

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


# generated keyword aliases still require the matching concrete datum classes and tags
KDatumScaffold = frozenset(
    (
        ("Plane", "moRefPlane_c", "Feature"),
        ("Sketch", "moOriginProfileFeature_c", "Sketch"),
    )
)


# the fallback represents the resolved native import in a standalone import part
def FindLocalOwner(
    ModelValue: NativeModel, Archive: SldprtArchive
) -> NativeFeature | None:
    if ModelValue.operations or not HasLocalHelpers(Archive, ModelValue.features):
        return None
    ImportValue = None
    for FeatureValue in ModelValue.features:
        if FeatureValue.kind in ("Notes", "Exploded Views"):
            continue
        if FeatureValue.kind in KLocalScaffold and FeatureValue.class_name in (
            "",
            FeatureValue.kind,
        ):
            continue
        if (
            (FeatureValue.kind, FeatureValue.class_name, FeatureValue.xml_tag)
            in KDatumScaffold
            and FeatureValue.native_stream == KResolvedFeaturesStream
            and FeatureValue.native_offset is not None
            and FeatureValue.object_id > 0
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
