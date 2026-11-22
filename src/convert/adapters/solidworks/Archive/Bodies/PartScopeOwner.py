from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a complete unit component binds its enclosing part while bounded records retain their frame identity
def PartScopeOwner(ContextValue: BodyContext, NodeValue: ArchiveNode) -> ArchiveNode:
    PartRoot = ContextValue.PartRootValue
    if PartRoot is not None and NodeValue.ClassValue == RuntimeClass(
        "moUnitComponent_c", 1
    ):
        return PartRoot
    return NodeValue


# broad archives need the same enclosing part guard at the actual unit owner field
def UsesPartOwner(
    ContextValue: BodyContext, NodeValue: ArchiveNode, RuleValue: NativeField
) -> bool:
    return RuleValue.ModeValue == "FrameOwner" or (
        RuleValue.NameValue == "owner"
        and PartScopeOwner(ContextValue, NodeValue) is not NodeValue
    )
