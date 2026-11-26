from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.History.CheckHistRefs import CheckHistRefs
from convert.adapters.solidworks.Archive.History.HistoryTypes import (
    KHistoryRootTypes,
    KVersionHistClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# validated streams require their actual root role and complete version history references
def CheckHistRoot(NodeValue: ArchiveNode | None) -> ArchiveNode:
    if NodeValue is None or NodeValue.ClassValue not in KHistoryRootTypes:
        raise BodyUnsupported("SOLIDWORKS history has an unsupported concrete root")
    if NodeValue.ClassValue == KVersionHistClass:
        CheckHistRefs(NodeValue)
    return NodeValue
