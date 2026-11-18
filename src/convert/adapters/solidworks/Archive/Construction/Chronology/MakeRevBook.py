from convert.adapters.solidworks.Archive.Construction.Chronology.MakeRevLog import (
    MakeRevLog,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionGraph import (
    RevisionGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# typed revision intentions must construct every collection and stamp without reading a saved header
def MakeRevBook(InputValue: RevisionBook) -> RevisionGraph:
    if type(InputValue) is not RevisionBook:
        raise ValueError("revision construction requires explicit typed intentions")
    UsersValue, CompaniesValue = (
        ArchiveNode(
            RuntimeClass("su_CStringArray", 0),
            {
                "values": tuple(
                    CStringValue(TextValue, True) for TextValue in TableValue
                )
            },
        )
        for TableValue in (InputValue.UsersValue, InputValue.CompaniesValue)
    )
    return RevisionGraph(
        UsersValue,
        CompaniesValue,
        ArchiveNode(
            RuntimeClass("suObList", 1),
            {
                "items": tuple(
                    MakeRevLog(InputValue, LogValue)
                    for LogValue in InputValue.LogsValue
                )
            },
        ),
    )
