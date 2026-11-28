from dataclasses import replace as ReplaceData

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Api.Fusion.SavedCuboid.ReadResave import GetCatalog, ReadResave


# malformed observer frames must reach the actual strict archive decoder and fail closed
@MarkTests.parametrize("Contrast", ("duplicate", "missing", "owner", "rank", "order"))
def TestResaveGuard(Contrast: str) -> None:
    Model = ReadDocument(ReadResave())
    Table, Catalog, TableSlots = GetCatalog(Model)
    Subjects = Catalog.Frame.Subjects
    assert Subjects is not None and len(Subjects) == len(TableSlots) + 1
    Other = BuildGraph(Model).OneClass("FusionComponent")
    Expected = ChangedRows(Subjects, Contrast, Other.ObjectId)
    Changed = SetSubjects(Model, Catalog, Expected)
    Payload = EmitParsed(Changed)
    Reopened = ReadDocument(Payload)
    ReTable, ReCatalog, ReSlots = GetCatalog(Reopened)
    assert (ReTable, ReSlots) == (Table, TableSlots)
    assert ReCatalog.Frame.Subjects == Expected
    with RaisesError(
        ValueError,
        match="^Native fixed rectangle parameter index disagrees with its table$",
    ):
        _ = OpenDocument(Payload, source_format="f3d", strict=True)


# each contrast changes only one aspect of the source observer inventory
def ChangedRows(
    Subjects: tuple[SubjectValue, ...], Contrast: str, OtherOwner: int
) -> tuple[SubjectValue, ...]:
    Leader, First, Second, *Remaining = Subjects
    if Contrast == "duplicate":
        return Leader, Second, Second, *Remaining
    if Contrast == "missing":
        return Leader, Second, *Remaining
    if Contrast == "owner":
        return (
            Leader,
            ReplaceData(First, Target=LocalRef(OtherOwner)),
            Second,
            *Remaining,
        )
    if Contrast == "rank":
        return Leader, ReplaceData(First, ObserverIndex=1), Second, *Remaining
    assert Contrast == "order"
    return Leader, Second, First, *Remaining


# the changed catalog frame stays inside the original segment and primary record
def SetSubjects(
    Model: DocumentModel, Catalog: NativeNode, Subjects: tuple[SubjectValue, ...]
) -> DocumentModel:
    return ReplaceData(
        Model,
        Segments=tuple(
            (
                ReplaceData(
                    Segment,
                    Records=tuple(
                        ChangeRecord(Record, Catalog, Subjects)
                        for Record in Segment.Records
                    ),
                )
                if Segment.Metadata.Header.SegmentId == Catalog.SegmentId
                else Segment
            )
            for Segment in Model.Segments
        ),
    )


# the mutation retains class schemas and edits only the selected primary frame
def ChangeRecord(
    Record: EntityRecord, Catalog: NativeNode, Subjects: tuple[SubjectValue, ...]
) -> EntityRecord:
    if Record.IsPrimary and Record.ObjectId == Catalog.ObjectId:
        return ReplaceData(Record, Frame=ReplaceData(Record.Frame, Subjects=Subjects))
    return Record
