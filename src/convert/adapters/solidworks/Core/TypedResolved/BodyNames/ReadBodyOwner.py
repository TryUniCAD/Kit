from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a selected chamfer needs the unique actual extrusion root
def ReadBodyOwner(
    LinkValue: NativeLink,
) -> ArchiveNode:
    BossValues = tuple(
        RequireNative(NodeValue, "moExtrusion_c")
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None and NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    if len(BossValues) != 1:
        raise ValueError("named body has no unique witnessed extrusion owner")
    return BossValues[0]
