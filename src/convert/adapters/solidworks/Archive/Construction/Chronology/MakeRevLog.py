from convert.adapters.solidworks.Archive.Construction.Chronology.MakeRevStamp import (
    MakeRevStamp,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import (
    RevisionLog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# log identity follows its actual node while event order and captions remain independent authored inputs
def MakeRevLog(BookValue: RevisionBook, InputValue: RevisionLog) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moLogs_c", 1),
        {
            "items": tuple(
                MakeRevStamp(BookValue, EventValue)
                for EventValue in InputValue.EventsValue
            ),
            "f48": FieldInt(InputValue.OwnerValue.FieldsValue, "f08"),
            "f50": CStringValue(InputValue.CaptionValue, True),
        },
    )
