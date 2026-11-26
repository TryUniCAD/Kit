from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# supplied root dependencies need actual concrete owners instead of matching labels on unresolved references
def RequireRootNode(NodeValue: ArchiveNode, ClassName: str) -> None:
    NodeValue = ArchiveNode.RequireNode(NodeValue)
    if type(
        NodeValue.ClassValue
    ) is not RuntimeClass or NodeValue.ClassValue != RuntimeClass(ClassName, 1):
        raise ValueError(f"part root requires a concrete schema one {ClassName}")
