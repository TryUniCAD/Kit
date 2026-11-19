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
    NeedConceptNode as Node,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText as Text,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.One import One
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.Rows import Rows


# authoring chronology and physical save identity must remain separate typed owners during blank recovery
def ReadBlankHeader(
    Root: ArchiveNode, History: HistoryInput
) -> tuple[HeaderInput, SelfFileInput]:
    Value = Node(Root, "moHeader_c").FieldsValue
    Authors = Rows(Node(Value["f10"], "su_CStringArray").FieldsValue["values"])
    Companies = Rows(Node(Value["f18"], "su_CStringArray").FieldsValue["values"])
    Logs = Rows(Node(Value["f20"], "suObList").FieldsValue["items"])
    Events = Rows(Node(One(Logs), "moLogs_c").FieldsValue["items"])
    Stamp = Node(One(Events), "moStamp_c").FieldsValue
    Require(
        Integer(Stamp["f18"]) == Integer(Value["f70"]) == History.CreatedAt
        and Text(Stamp["f20"]) == History.CommentText,
        "blank creation and comment provenance disagree",
    )
    Header = HeaderInput(
        Text(One(Authors)),
        Text(One(Companies)),
        Text(Stamp["f20"]),
        Integer(Value["f70"]),
        Integer(Value["f50"]),
        Integer(Value["f48"]),
    )
    File = Node(Value["f38"], "moExtObject_c").FieldsValue
    Shared = Fields(File["shared"])
    Path = Text(Node(Shared["h18"], "moCStringHandle_c").FieldsValue["value"])
    return Header, SelfFileInput(Path, Integer(File["f60"]))
