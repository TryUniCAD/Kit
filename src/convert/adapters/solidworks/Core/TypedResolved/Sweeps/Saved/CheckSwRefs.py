from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwHist import (
    ReadSwList,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.SwMapClass import (
    SwMapClass,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)


# saved selection caches must describe the two exact face roles of their own body
def ReadSwChoice(SweepValue: ArchiveNode, FieldName: str) -> tuple[ArchiveNode, ...]:
    ChoiceValue = NativeRecord(SweepValue.FieldsValue.get(FieldName))
    if ChoiceValue.get("f68") is not SweepValue:
        raise ValueError("SOLIDWORKS saved sweep chooser has a foreign feature")
    return ReadSwList(ChoiceValue.get("f48"))


# native side and end picks must stay local to the actual current configuration and creation stamp
def CheckSwSide(
    RepValue: ArchiveNode, SourceValue: NativeFileRef, FeatureId: int, CreatedAt: int
) -> None:
    DataValue = NativeRecord(RepValue.FieldsValue.get("f10"))
    RefValue = RequireNative(DataValue.get("f10"), "moFR_c")
    External = RequireNative(RefValue.FieldsValue.get("f08"), "moExtObject_c")
    SharedValue = NativeRecord(External.FieldsValue.get("shared"))
    PathValue = RequireNative(
        SharedValue.get("h18"), "moCStringHandle_c"
    ).FieldsValue.get("f08")
    NameValue = RequireNative(
        SharedValue.get("h10"), "moCStringHandle_c"
    ).FieldsValue.get("f08")
    if (
        DataValue.get("f08") is not None
        or RefValue.FieldsValue.get("f10") != {"f00": FeatureId, "f08": CreatedAt}
        or NativeRecord(External.FieldsValue.get("refcfg")).get("f08")
        != SourceValue.ConfigValue
        or (PathValue, NameValue) != (SourceValue.PathValue, SourceValue.NameValue)
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep face selection links a foreign document or producer"
        )


# all reachable face selection representations must belong to witnessed local choices
def CheckSwRefs(GraphValue: SwReadGraph, SourceValue: NativeFileRef) -> None:
    SweepValue = GraphValue.FeatureValue
    (FirstChoice,) = ReadSwChoice(SweepValue, "f4a8")
    (SecondChoice,) = ReadSwChoice(SweepValue, "f4c0")
    if FirstChoice is SecondChoice or ReadSwChoice(SweepValue, "f4b0"):
        raise ValueError(
            "SOLIDWORKS saved sweep has an alternate retained face selection"
        )
    NativeId = NativeNodeId(SweepValue)
    CreatedAt = DatumTime(GraphValue.LinkValue.ConfigValue.HeaderValue, NativeId)
    ForSides: set[int] = set()
    ForEnds: set[int] = set()
    for ChoiceValue in (FirstChoice, SecondChoice):
        FacesValue = ReadSwList(
            RequireNative(ChoiceValue, "moPerBodyChooserData_c").FieldsValue.get("f08")
        )
        if len(FacesValue) != 2 or ReadSwList(ChoiceValue.FieldsValue.get("f28")):
            raise ValueError("SOLIDWORKS saved sweep has an alternate face classifier")
        for FaceValue in FacesValue:
            for RepValue in ReadFaceReps(FaceValue):
                CheckSwSide(RepValue, SourceValue, NativeId, CreatedAt)
                (
                    ForSides
                    if RepValue.ClassValue.NameValue == "moSweepSideSurfIdRep_c"
                    else ForEnds
                ).add(id(RepValue))
    MapValue = GraphValue.LinkValue.ResolvedValue.MapValue
    if (
        ForSides
        != {id(Value) for Value in SwMapClass(MapValue, "moSweepSideSurfIdRep_c")}
        or ForEnds
        != {id(Value) for Value in SwMapClass(MapValue, "moEndFaceSurfIdRep_c")}
        or len(ForSides) != 2
        or len(ForEnds) != 3
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep has unowned face selection representations"
        )


# every nonnull face selector must belong to the witnessed side and end vocabulary
def ReadFaceReps(FaceValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    Fields = RequireNative(FaceValue, "moFaceRef_c").FieldsValue
    RowsValue = NativeRows(Fields.get("f10"))
    if (
        len(RowsValue) != Fields.get("f08")
        or Fields.get("f40") is not None
        or Fields.get("has_f18")
    ):
        raise ValueError("SOLIDWORKS saved sweep has a foreign face reference tail")
    Values = tuple(
        RequireNative(RowValue["f08"])
        for RowValue in RowsValue
        if RowValue.get("f08") is not None
    )
    for RepValue in Values:
        NameValue = RepValue.ClassValue.NameValue
        Flags = (RepValue.FieldsValue.get("f38"), RepValue.FieldsValue.get("f3c"))
        if (NameValue == "moSweepSideSurfIdRep_c" and Flags == (1, 1)) or (
            NameValue == "moEndFaceSurfIdRep_c" and Flags in ((0, 0), (1, 0))
        ):
            continue
        raise ValueError("SOLIDWORKS saved sweep has an alternate face reference")
    return Values
