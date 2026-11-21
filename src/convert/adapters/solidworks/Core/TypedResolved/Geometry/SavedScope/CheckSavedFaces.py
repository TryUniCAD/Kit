from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevSelf import (
    CheckRevSelf,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevChoices import (
    ReadRevChoices,
)


# retained choosers may describe only the two ends and four sides of the same producer
def CheckSavedFaces(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    LoopValue: LineLoop,
    ConfigName: str,
) -> None:
    ChooserValue = NativeRecord(BossValue.FieldsValue.get("f4b0"))
    if ChooserValue.get("f68") is not BossValue or not IsLineState(
        ChooserValue.get("f48")
    ):
        raise ValueError("SOLIDWORKS saved first boss has an additional chooser input")
    FeatureId = NativeNodeId(BossValue)
    HeaderValue = LinkValue.ConfigValue.HeaderValue
    TopHeader = ReadHeaderGraph(
        Archive.require("Header2"), LinkValue.ConfigValue.VersionValue
    )
    EventValue = DatumTime(HeaderValue, FeatureId)
    if DatumTime(TopHeader, FeatureId) != EventValue:
        raise ValueError("SOLIDWORKS saved first boss has a different creation owner")
    First, Second = ReadRevChoices(LinkValue, BossValue, {FeatureId: EventValue}, 6)
    LineIds = {LineValue.PermanentId for LineValue in LoopValue.LinesValue}
    for EndId, FaceValues in enumerate((First, Second)):
        if (
            len(FaceValues) != 5
            or [(Value.IsEnd, Value.MarkValue) for Value in FaceValues if Value.IsEnd]
            != [(True, EndId)]
            or {Value.MarkValue for Value in FaceValues if not Value.IsEnd} != LineIds
        ):
            raise ValueError(
                "SOLIDWORKS saved first boss has alternate output face roles"
            )
    if len({Value.Representation for Value in (*First, *Second)}) != 10:
        raise ValueError(
            "SOLIDWORKS saved first boss repeats output face representations"
        )
    CheckRevSelf(HeaderValue, (*First, *Second))
    CheckRevSelf(TopHeader, (*First, *Second))
    External = First[0].ExternalValue
    if NativeRecord(External.FieldsValue.get("refcfg")).get("f08") != ConfigName:
        raise ValueError(
            "SOLIDWORKS saved first boss faces do not own the active configuration"
        )
