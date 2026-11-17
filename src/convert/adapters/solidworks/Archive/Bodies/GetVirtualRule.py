from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# virtual field dispatch must be grounded for the concrete owner rather than its base schema
def GetVirtualRule(
    ContextValue: BodyContext, NodeValue: ArchiveNode, RuleValue: NativeField
) -> str | bool | None:
    Lookup = (NodeValue.ClassValue.NameValue, RuleValue.MaskValue)
    if Lookup not in ContextValue.VirtualValue:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS body virtual slot {RuleValue.MaskValue:#x} for {Lookup[0]}"
        )
    return ContextValue.VirtualValue[Lookup]
