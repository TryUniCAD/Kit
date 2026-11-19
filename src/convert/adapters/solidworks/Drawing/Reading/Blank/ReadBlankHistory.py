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


# originating build and locale facts must come from the complete independent native history owner
def ReadBlankHistory(Root: ArchiveNode) -> HistoryInput:
    Value = Node(Root, "moVersionHistory_c").FieldsValue
    States = Rows(Value["states"])
    Require(
        Integer(Value["n"]) == len(States) == 1,
        "blank history has multiple or missing version events",
    )
    State = Fields(One(States))["st"]
    StateFields = Fields(State)
    Stamp = Fields(StateFields["f08"])
    Codes = Node(StateFields["f38"], "moDateCodeHistory_c").FieldsValue
    CodesRows = Rows(Codes["states"])
    Require(
        Integer(Codes["n"]) == len(CodesRows) == 1,
        "blank history has multiple or missing build events",
    )
    Build = Integer(Fields(Fields(One(CodesRows))["st"])["f08"])
    Require(Value["f3c"] in (0, 1), "blank history has invalid CJK state")
    return HistoryInput(
        Integer(Stamp["f18"]),
        Text(Stamp["f20"]),
        Build,
        Integer(Value["f30"]),
        Integer(Value["f38"]),
        bool(Value["f3c"]),
    )
