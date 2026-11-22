from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.SwMapClass import (
    SwMapClass,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)

# this reader scope accounts for the ordinary system roots and only the one editable sweep
KSwSavedRoots = (
    "moCommentsFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moDocsFolder_c",
    "moDetailCabinet_c",
    "moSurfaceBodyFolder_c",
    "moSolidBodyFolder_c",
    "moEnvFolder_c",
    "moInkMarkupFolder_c",
    "moEqnFolder_c",
    "moMaterialFolder_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moOriginProfileFeature_c",
    "moProfileFeature_c",
    "moProfileFeature_c",
    "moSweep_c",
)


# counted lists must retain actual single graph identities before checking local ownership
def ReadSwList(RecordValue: object) -> tuple[ArchiveNode, ...]:
    ListValue = NativeRecord(RecordValue)
    RowsValue = NativeRows(ListValue.get("items"))
    if ListValue.get("n") != len(RowsValue):
        raise ValueError("SOLIDWORKS saved sweep has an incomplete owner list")
    return tuple(RequireNative(RowValue.get("o")) for RowValue in RowsValue)


# standard saved history names each actual feature in the same local ordered document
def CheckSwHist(GraphValue: SwReadGraph, LabelsValue: SweepLabels) -> None:
    LinkValue = GraphValue.LinkValue
    RootsValue = tuple(
        RequireNative(Value) for Value in LinkValue.ResolvedValue.RootsValue
    )
    FeatureValues = (
        GraphValue.SectionValue.FeatureValue,
        GraphValue.PathValue.FeatureValue,
        GraphValue.FeatureValue,
    )
    if (
        tuple(Value.ClassValue.NameValue for Value in RootsValue) != KSwSavedRoots
        or tuple(ReadNativeName(Value) for Value in FeatureValues)
        != (LabelsValue.SectionName, LabelsValue.SketchName, LabelsValue.FeatureName)
        or any(Value.FieldsValue.get("hidden") for Value in FeatureValues)
    ):
        raise ValueError("SOLIDWORKS saved sweep has an alternate feature inventory")
    (HistoryValue,) = SwMapClass(LinkValue.ResolvedValue.MapValue, "moHistoryFolder_c")
    ItemsValue = ReadSwList(HistoryValue.FieldsValue.get("f3c8"))
    if ItemsValue != SwMapClass(
        LinkValue.ResolvedValue.MapValue, "moHistoryFeatItemData_c"
    ):
        raise ValueError("SOLIDWORKS saved sweep history contains foreign records")
    for ItemValue, FeatureValue in zip(ItemsValue, FeatureValues, strict=True):
        RefValue = RequireNative(ItemValue.FieldsValue.get("f48"), "moCompFeature_c")
        Component = RequireNative(RefValue.FieldsValue.get("f58"), "moUnitComponent_c")
        FeatureId = NativeNodeId(FeatureValue)
        if (
            RefValue.FieldsValue.get("ff0")
            != {
                "f00": FeatureId,
                "f08": DatumTime(LinkValue.ConfigValue.HeaderValue, FeatureId),
            }
            or RefValue.FieldsValue.get("f20") != 0
            or Component.FieldsValue.get("has_ext") != 0
            or Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep history has a foreign feature owner"
            )
