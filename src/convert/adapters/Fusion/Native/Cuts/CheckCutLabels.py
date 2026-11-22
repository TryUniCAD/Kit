from convert.adapters.Fusion.Native.Cuts.CheckCutFace import CheckCutFace
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# every physical face and the sole body require their exact native feature identity
def CheckCutLabels(
    Table: LiveTable,
    BodyRef: int,
    Rings: tuple[tuple[KJournalVector, ...], ...],
    Labels: tuple[FeatureTag, ...],
    BodyTag: FeatureTag,
) -> None:
    Expected = {
        FaceValue.FaceRef: Labels[CheckCutFace(Table, FaceValue, Rings)]
        for FaceValue in ReadBodyFaces(Table, BodyRef)
    }
    Expected[BodyRef] = BodyTag
    for Reference in Table.LiveSlots:
        Entity = Table.Entities[Reference]
        if not isinstance(Entity, TagAttrib):
            continue
        Owner = StableRef(Table, Entity.Links.OwnerRef)
        TagValue = Expected.pop(Owner, None)
        if TagValue is None or Entity.Groups != (TagValue,):
            raise ValueError(
                "Native cut topology labels disagree with authored feature ownership"
            )
    if Expected:
        raise ValueError("Native cut is missing physical topology labels")
