from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionKinds import (
    KRevisionKinds,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# source logs need actual unique graph owners rather than guessed names or detached saved identifiers
def CheckLogOwners(ModelValue: ArchiveNode, InputValue: RevisionBook) -> None:
    RequireRootNode(ModelValue, "moPart_c")
    SeenValues: set[int] = set()
    for LogValue in InputValue.LogsValue:
        OwnerValue = LogValue.OwnerValue
        if OwnerValue.ClassValue.NameValue not in KRevisionKinds:
            raise ValueError("revision owner class is outside the mapped part scope")
        RequireRootNode(OwnerValue, OwnerValue.ClassValue.NameValue)
        Identifier = FieldInt(OwnerValue.FieldsValue, "f08")
        if not 0 <= Identifier <= 0x7FFFFFFF or Identifier in SeenValues:
            raise ValueError("revision owners require unique persistent identifiers")
        SeenValues.add(Identifier)
        NameValue = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f18"])
        RequireRootNode(NameValue, "moNodeName_c")
        if (
            OwnerValue is not ModelValue
            and OwnerValue.FieldsValue.get("owner") is not ModelValue
        ):
            raise ValueError("revision feature must belong to the actual modeled part")
    RootValues = tuple(
        LogValue
        for LogValue in InputValue.LogsValue
        if LogValue.OwnerValue is ModelValue
    )
    if (
        len(RootValues) != 1
        or not RootValues[0].EventsValue
        or RootValues[0].EventsValue[0].OperationValue != "created"
    ):
        raise ValueError("part revisions require its one actual model creation event")
