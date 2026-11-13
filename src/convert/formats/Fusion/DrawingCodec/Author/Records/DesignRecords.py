from convert.formats.Fusion.DrawingCodec.Author.Defaults.ContainerRecords import (
    KContainerRecords,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KFirstTracked,
    KTrackedSpan,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Model.TrackedEdge import TrackedEdge
from convert.formats.Fusion.DrawingCodec.Author.Records.ComponentRecords import (
    ComponentRecord,
    InstanceRecord,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.SourceRecords import (
    FileRecord,
    SheetRecord,
    SheetsRecord,
    SourceRecord,
    TrackedRoot,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.TrackedRecords import (
    TrackedRecords,
)
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def DesignRecords(
    SpecValue: DrawingSpec, FileName: str, History: SaveState
) -> tuple[EntityRecord, ...]:
    FirstIds = TrackedIds(SpecValue.Annotations)
    SheetId = SheetHandle(SpecValue.LayoutHandle)
    LinkRole = SpecValue.Identity.LinkRole
    Built = [
        ComponentRecord(SpecValue.Identity, History.CycleColor),
        InstanceRecord(SpecValue.Identity, History.InstanceGates),
        FileRecord(FileName),
        TrackedRoot(FirstIds),
        SheetsRecord(SheetId),
        SourceRecord(SheetId, LinkRole, SpecValue.Design, History.PropertyColumns),
        SheetRecord(SheetId, SpecValue.Sheet.SheetName, SpecValue.Design),
    ]
    for FirstId, EdgeValue in zip(FirstIds, SpecValue.Annotations, strict=True):
        Built.extend(TrackedRecords(FirstId, EdgeValue, SpecValue.Design))
    return tuple(sorted((*KContainerRecords, *Built), key=RecordKey))


def RecordKey(Record: EntityRecord) -> tuple[int, bool]:
    return Record.ObjectId, not Record.IsPrimary


def SheetHandle(LayoutHandle: int) -> str:
    return f"{LayoutHandle:X}"


def TrackedIds(Annotations: tuple[TrackedEdge, ...]) -> tuple[int, ...]:
    Result: list[int] = []
    NextFree = KFirstTracked
    for EdgeValue in Annotations:
        FirstId = NextFree if EdgeValue.FirstId is None else EdgeValue.FirstId
        if type(FirstId) is not int or FirstId < NextFree:
            raise ValueError("Tracked drawing edge identities overlap or are reserved")
        Result.append(FirstId)
        NextFree = FirstId + KTrackedSpan
    return tuple(Result)


def DesignNextId(Annotations: tuple[TrackedEdge, ...], History: SaveState) -> int:
    FirstIds = TrackedIds(Annotations)
    NextFree = FirstIds[-1] + KTrackedSpan if FirstIds else KFirstTracked
    if History.DesignNextId is None:
        return NextFree
    if type(History.DesignNextId) is not int or History.DesignNextId < NextFree:
        raise ValueError("Fusion drawing next identity collides with its records")
    return History.DesignNextId
