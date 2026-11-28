from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode as NeedNode,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText as ReadText,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.One import OnlyItem
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.Rows import ReadRecordRows


# authoring chronology and physical save identity must remain separate typed owners during blank recovery
def ReadBlankHeader(
    HeaderRoot: ArchiveNode, History: HistoryInput
) -> tuple[HeaderInput, SelfFileInput]:
    Value = NeedNode(HeaderRoot, "moHeader_c").FieldsValue
    Authors = ReadRecordRows(
        NeedNode(Value["f10"], "su_CStringArray").FieldsValue["values"]
    )
    Companies = ReadRecordRows(
        NeedNode(Value["f18"], "su_CStringArray").FieldsValue["values"]
    )
    LogRecords = ReadRecordRows(NeedNode(Value["f20"], "suObList").FieldsValue["items"])
    Events = ReadRecordRows(
        NeedNode(OnlyItem(LogRecords), "moLogs_c").FieldsValue["items"]
    )
    Stamp = NeedNode(OnlyItem(Events), "moStamp_c").FieldsValue
    Require(
        Integer(Stamp["f18"]) == Integer(Value["f70"]) == History.CreatedAt
        and ReadText(Stamp["f20"]) == History.CommentText,
        "blank creation and comment provenance disagree",
    )
    Header = HeaderInput(
        ReadText(OnlyItem(Authors)),
        ReadText(OnlyItem(Companies)),
        ReadText(Stamp["f20"]),
        Integer(Value["f70"]),
        Integer(Value["f50"]),
        Integer(Value["f48"]),
    )
    FileRecord = NeedNode(Value["f38"], "moExtObject_c").FieldsValue
    Shared = Fields(FileRecord["shared"])
    PathRecord = ReadText(
        NeedNode(Shared["h18"], "moCStringHandle_c").FieldsValue["value"]
    )
    return Header, SelfFileInput(PathRecord, Integer(FileRecord["f60"]))
