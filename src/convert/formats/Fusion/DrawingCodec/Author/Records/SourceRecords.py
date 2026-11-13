from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KBaseColumns,
    KSheetOrder,
    KTitleBlockId,
    KZeroGuid,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.PartColumns import (
    KPartColumns,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.ColumnIdent import ColumnIdent
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.PartColumn import PartColumn
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import (
    ChildTail,
    MakeRecord,
)
from convert.formats.Fusion.DrawingCodec.Model.CheckDatabase import KFileClass
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KSheetsGuid = "D67E6C0E-1316-4EF5-8967-9ACE29B9DF61"

KSheetGuid = "632EEBFC-0412-4AA4-9CF1-69C94F55C038"

KSourceGuid = "3EAD2723-67C3-4C8E-9B9E-1208F04C4C44"

KFilterValue = ValueObject(
    (
        EntityGroup(
            "62B5B83C-EDDB-483D-BCBD-1DB17B8386F0",
            (
                NamedValue("compFilterStr", ""),
                NamedValue("comps", ValueMap(())),
                NamedValue("isExtra", False),
            ),
        ),
    )
)


def FileRecord(FileName: str) -> EntityRecord:
    return MakeRecord(
        22,
        (EntityGroup(KFileClass, (NamedValue("persistedFileName", FileName),)),),
        RootId="ExternalDWG",
    )


def TrackedRoot(FirstIds: tuple[int, ...]) -> EntityRecord:
    Children = tuple(LocalRef(ObjectId) for ObjectId in FirstIds)
    return MakeRecord(24, ChildTail(None, Children), IsPrimary=False)


def SheetsRecord(SheetId: str) -> EntityRecord:
    Fields = (NamedValue("activeSheetId", SheetId), NamedValue("sketchIndex", 0))
    return MakeRecord(26, (EntityGroup(KSheetsGuid, Fields),))


def SheetRecord(SheetId: str, SheetName: str, Design: DesignTarget) -> EntityRecord:
    Fields = (
        NamedValue("componentOccPath", f"R{Design.ComponentId}-"),
        NamedValue("displayName", SheetName),
        NamedValue("isDisassociated", False),
        NamedValue("isOutOfDate", False),
        NamedValue("largeThumbnail", SheetId + "_large.png"),
        NamedValue("sheetId", SheetId),
        NamedValue("sheetOrder", KSheetOrder),
        NamedValue("thumbnail", SheetId + "_small.png"),
        NamedValue("titleBlockDesignId", KTitleBlockId),
        NamedValue("titleBlockOccPath", "root"),
        NamedValue("titleBlockPropertyOverriden", False),
    )
    return MakeRecord(43, (EntityGroup(KSheetGuid, Fields),))


def SourceRecord(
    SheetId: str, LinkRole: str, Design: DesignTarget, PropertyColumns: bool
) -> EntityRecord:
    Owner = (Design.InstanceId, Design.ComponentId)
    Visible = ValueMap(
        (
            ValuePair(ValueSeries((*Owner, Design.BodiesId)), True),
            ValuePair(ValueSeries((*Owner, Design.SketchesId)), False),
        )
    )
    Fields = (
        NamedValue("animationMarker", ValuePair("", 0.0)),
        NamedValue("bodyVisMap", Visible),
        NamedValue("designAssetGuid", KZeroGuid),
        NamedValue("designId", 1),
        NamedValue("index", 1),
        NamedValue("isComponentFilterUpdated", True),
        NamedValue("modelDocLinkName", LinkRole),
        NamedValue("newComponentFilter", KFilterValue),
        NamedValue("partsListColumns", SourceColumns(PropertyColumns)),
        NamedValue("partsLists", LocalRef(40)),
        NamedValue("partslistType", 0),
        NamedValue("referenceDesignatorsList", None),
        NamedValue("sheetIds", ValueSeries((SheetId,))),
        NamedValue("silkscreenBodiesVisMap", ValueMap(())),
        NamedValue("silkscreensList", ValueMap(())),
        NamedValue("sourceComponentOccPathStr", ""),
        NamedValue("sourceId", "1_Component"),
        NamedValue("sourceType", 4),
    )
    return MakeRecord(39, (EntityGroup(KSourceGuid, Fields),))


def SourceColumns(PropertyColumns: bool) -> ValueSeries:
    Columns = KPartColumns[:KBaseColumns]
    if PropertyColumns:
        Columns += tuple(sorted(KPartColumns[KBaseColumns:], key=ColumnName))
    return ValueSeries(
        tuple(ValuePair(ColumnIdent(Column), Column.Shown) for Column in Columns)
    )


def ColumnName(Column: PartColumn) -> str:
    return Column.DisplayName
