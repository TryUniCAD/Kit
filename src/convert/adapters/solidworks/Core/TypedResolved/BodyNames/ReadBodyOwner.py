from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# optional revolve naming must retain the actual selected feature without widening the existing extrusion owner path
def ReadBodyOwner(
    LinkValue: NativeLink, RevolveValue: ArchiveNode | None
) -> ArchiveNode:
    BossValues = tuple(
        RequireNative(NodeValue, "moExtrusion_c")
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None and NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    if RevolveValue is not None:
        RequireNative(RevolveValue, "moRevolution_c")
        if (
            BossValues
            or sum(
                NodeValue is RevolveValue
                for NodeValue in LinkValue.ResolvedValue.RootsValue
            )
            != 1
        ):
            raise ValueError("named revolve is not its unique actual root owner")
        BossValues = (RevolveValue,)
    if len(BossValues) != 1:
        raise ValueError("named body has no unique witnessed extrusion owner")
    return BossValues[0]
