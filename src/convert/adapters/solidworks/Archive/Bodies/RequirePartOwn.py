from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# direct field dispatch is limited to the measured inline owner of the mapped part
def RequirePartOwn(
    ContextValue: BodyContext, NodeValue: ArchiveNode, RuleValue: NativeField
) -> RuntimeClass:
    if (
        ContextValue.PartRootValue is not NodeValue
        or RuleValue.NameValue != "f1018"
        or RuleValue.TypeValue != "moSheetMetalMaster_c"
    ):
        raise BodyUnsupported("unqualified directly owned configuration field")
    return RuntimeClass(RuleValue.TypeValue, 1)
