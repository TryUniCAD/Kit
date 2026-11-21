from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadChooserPair import (
    ReadChooserPair,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadFaceReps import (
    ReadFaceReps,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# mirrored chooser rows share their exact resolved surface reps and actual native producer
def ReadThinRefs(
    LinkValue: NativeLink, FeatureValue: ArchiveNode, ConfigName: str
) -> None:
    Chooser = NativeRecord(FeatureValue.FieldsValue.get("f4b0"))
    if Chooser.get("f68") is not FeatureValue or not IsLineState(Chooser.get("f48")):
        raise ValueError("SOLIDWORKS saved thin has an alternate body chooser")
    FirstPair = ReadChooserPair(LinkValue, FeatureValue, "f4a8")
    OtherPair = ReadChooserPair(LinkValue, FeatureValue, "f4c0")
    FacesValue = tuple(ReadFaceReps(FaceValue) for FaceValue in FirstPair)
    if len(set((*FirstPair, *OtherPair))) != 4 or FacesValue != tuple(
        map(ReadFaceReps, OtherPair)
    ):
        raise ValueError("SOLIDWORKS saved thin surface chooser identities differ")
    RepsValue = tuple(RepValue for FaceValue in FacesValue for RepValue in FaceValue)
    Expected = (
        "moEndFaceSurfIdRep_c",
        "moThinOffsetSurfIdRep_c",
        "moThinClosingSurfIdRep_c",
        "moFromSktEntSurfIdRep_c",
        "moThinClosingSurfIdRep_c",
    )
    if len(set(RepsValue)) != 10 or any(
        tuple(RepValue.ClassValue.NameValue for RepValue in FaceValue) != Expected
        for FaceValue in FacesValue
    ):
        raise ValueError(
            "SOLIDWORKS saved thin has unsupported face representation roles"
        )
    KeyValue = NativeNodeId(FeatureValue)
    Sources = tuple(ReadThinRef(RepValue, KeyValue) for RepValue in RepsValue)
    ExtValues = {ExtValue for _, ExtValue in Sources}
    if (
        len(ExtValues) != 1
        or NativeRecord(next(iter(ExtValues)).FieldsValue.get("refcfg")).get("f08")
        != ConfigName
    ):
        raise ValueError(
            "SOLIDWORKS saved thin surface chooser crosses its actual configuration"
        )
    CheckTreeAlias(
        LinkValue,
        (*RepsValue, *(SourceValue for SourceValue, _ in Sources), *ExtValues),
    )


# surface keepers resolve the producer reference through the stored native object key
def ReadThinRef(
    RepValue: ArchiveNode, FeatureId: int
) -> tuple[ArchiveNode, ArchiveNode]:
    Keeper = NativeRecord(RepValue.FieldsValue.get("f10"))
    Source = RequireNative(Keeper.get("f10"), "moFR_c")
    if (
        Keeper.get("f08") is not None
        or NativeRecord(Source.FieldsValue.get("f10")).get("f00") != FeatureId
    ):
        raise ValueError("SOLIDWORKS saved thin face has an unresolved native producer")
    return Source, RequireNative(Source.FieldsValue.get("f08"), "moExtObject_c")
