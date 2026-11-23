from convert.adapters.freecad.BodyLineage.BoxNativeOwner import FindBoxObject
from convert.adapters.freecad.Native import (
    LoadNative,
    NativeArchive,
    NativeMeta,
    NativeObject,
    NativeSource,
)
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep


# a reusable stock input must be an actual primitive from the same retained source tree
def ReadStockSource(
    Document: CadDocument, FeatureId: str
) -> tuple[NativeArchive, NativeObject, FeatureStep]:
    Source = Document.source
    Present = tuple(
        Value for Value in Document.feature_timeline if Value.id == FeatureId
    )
    PairValue = NativeDocPair(Document)
    if (
        Source.format_id != "freecad.fcstd"
        or Source.container_version != "1"
        or Source.attributes != {"freecad_schema_version": "4"}
        or str(Document.units) != "mm"
        or Document.assembly is not None
        or Document.DrawingValue is not None
        or len(Present) != 1
        or PairValue is None
        or PairValue[0].data is None
        or PairValue[0].sha256 != Source.sha256
    ):
        raise ValueError("FreeCAD stock requires its exact retained part source")
    DataValue = PairValue[0].data
    ArchiveValue = LoadNative(DataValue)
    if NativeSource(
        DataValue, Source.path, ArchiveValue
    ) != Source or Document.metadata.get("freecad") != NativeMeta(
        ArchiveValue, None, {}
    ):
        raise ValueError("FreeCAD stock source metadata disagrees with its archive")
    FeatureValue = Present[0]
    Definition = FeatureValue.definition
    if (
        type(Definition) is not NativeFeature
        or Definition.format_id != Source.format_id
        or Definition.type_id != "Part::Box"
        or Definition.object_data != FeatureValue.attributes.get("freecad")
        or FeatureValue.suppressed
        or FeatureValue.input_feature_ids
        or FeatureValue.selection_ids
        or FeatureValue.sketch_id is not None
    ):
        raise ValueError("FreeCAD stock requires an actual independent Part::Box")
    OwnerValue = FindBoxObject(ArchiveValue, Definition.object_data, "Part::Box")
    if (
        OwnerValue.touched
        or OwnerValue.dependencies
        or FeatureId != f"freecad:feature:{OwnerValue.name}"
        or FeatureValue.provenance is None
        or FeatureValue.provenance.native_id != OwnerValue.name
    ):
        raise ValueError("FreeCAD stock differs from its actual primitive owner")
    return ArchiveValue, OwnerValue, FeatureValue
