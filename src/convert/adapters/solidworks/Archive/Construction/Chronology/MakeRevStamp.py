from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import (
    RevisionEvent,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# revision stamp attribution must join explicit semantic names rather than reuse captured numeric indices
def MakeRevStamp(BookValue: RevisionBook, InputValue: RevisionEvent) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moStamp_c", 1),
        {
            "f08": {"created": 0, "modified": 1}[InputValue.OperationValue],
            "f0c": BookValue.UsersValue.index(InputValue.UserName),
            "f10": BookValue.CompaniesValue.index(InputValue.CompanyName),
            "f18": InputValue.EventAt,
            "f20": CStringValue(InputValue.CommentText, True),
        },
    )
