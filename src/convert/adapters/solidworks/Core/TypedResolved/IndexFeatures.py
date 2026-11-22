from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatLayouts import (
    KPatVirtuals,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# proven feature dispatch identifies resolved roots without scanning strings or manufacturing missing tree rows
def IndexFeatures(
    LinkValue: NativeLink, *, PartPattern: bool = False
) -> dict[int, ArchiveNode]:
    ResultValue: dict[int, ArchiveNode] = {}
    for RootValue in LinkValue.ResolvedValue.RootsValue:
        NodeValue = RequireNative(RootValue)
        ClassSlot = (NodeValue.ClassValue.NameValue, 0x3E8)
        TargetValue = KResolvedVirtuals.get(ClassSlot)
        if PartPattern:
            TargetValue = KPatVirtuals.get(ClassSlot, TargetValue)
        if TargetValue not in (
            "moFeature_c.SerializeXmlData",
            "moRefPlane_c.SerializeXmlData",
        ):
            raise ValueError("typed resolved root lacks proven feature dispatch")
        NativeId = NativeNodeId(NodeValue)
        if NativeId in ResultValue:
            raise ValueError(
                "typed resolved features have duplicate persistent identities"
            )
        ResultValue[NativeId] = NodeValue
    return ResultValue
