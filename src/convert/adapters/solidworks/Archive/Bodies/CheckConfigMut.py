from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.External.CheckExtFields import (
    CheckExtFields,
)
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# cyclic reference backlinks become available only after the containing node finishes loading
def CheckConfigMut(
    ContextValue: BodyContext, ScopeValue: FieldScope, NodeValue: ArchiveNode
) -> None:
    Parents = ContextValue.UsageValue.SchemaPath[:-1]
    FlagsValue = ContextValue.FlagsValue
    if (
        NodeValue.ClassValue != RuntimeClass("moExtFeature_c", 1)
        or not Parents
        or (Parents[0], Parents[-1]) != ("moAssembly_c", "moReference_c")
        or any(
            FlagsValue.get(NameValue, 0)
            for NameValue in ("plain_cstring_names", "owner_is_drawing", "conditions")
        )
    ):
        raise BodyUnsupported(
            "unsupported native configuration external feature owner or context"
        )
    CheckExtFields(ScopeValue.FieldsValue)
    Reference = ScopeValue.FieldsValue["f50"]
    if not isinstance(Reference, ArchiveNode) or Reference.ClassValue != RuntimeClass(
        "moReference_c", 1
    ):
        raise BodyUnsupported(
            "configuration external feature requires its concrete occurrence reference"
        )
    ContextValue.PendingNodes.append(NodeValue)
