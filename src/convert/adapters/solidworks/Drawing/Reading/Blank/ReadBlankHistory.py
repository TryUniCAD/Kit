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


# originating build and locale facts must come from the complete independent native history owner
def ReadDrawHist(HistoryRoot: ArchiveNode) -> HistoryInput:
    Value = NeedNode(HistoryRoot, "moVersionHistory_c").FieldsValue
    States = ReadRecordRows(Value["states"])
    Require(
        Integer(Value["n"]) == len(States) == 1,
        "blank history has multiple or missing version events",
    )
    State = Fields(OnlyItem(States))["st"]
    StateFields = Fields(State)
    Stamp = Fields(StateFields["f08"])
    Codes = NeedNode(StateFields["f38"], "moDateCodeHistory_c").FieldsValue
    CodesRows = ReadRecordRows(Codes["states"])
    Require(
        Integer(Codes["n"]) == len(CodesRows) == 1,
        "blank history has multiple or missing build events",
    )
    Build = Integer(Fields(Fields(OnlyItem(CodesRows))["st"])["f08"])
    Require(Value["f3c"] in (0, 1), "blank history has invalid CJK state")
    return HistoryInput(
        Integer(Stamp["f18"]),
        ReadText(Stamp["f20"]),
        Build,
        Integer(Value["f30"]),
        Integer(Value["f38"]),
        bool(Value["f3c"]),
    )
