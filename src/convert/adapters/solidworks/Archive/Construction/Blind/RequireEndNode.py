from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# constructor references must exclude unresolved placeholders and unrelated class or schema identities
def RequireEndNode(NodeValue: object, ClassName: str) -> ArchiveNode:
    ActualValue = ArchiveNode.RequireNode(NodeValue)
    if ActualValue.ClassValue != RuntimeClass(ClassName, 1):
        raise ValueError(f"blind construction expected concrete schema one {ClassName}")
    return ActualValue
