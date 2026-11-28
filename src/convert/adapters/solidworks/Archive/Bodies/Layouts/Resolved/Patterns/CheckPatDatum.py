from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# pattern datum roles must be checked even when a preceding node already defined the referenced body
def CheckPatDatum(ScopeValue: FieldScope) -> None:
    FieldsValue = ScopeValue.FieldsValue
    for SlotName, ClassName in (
        ("f1288", "moLineRef_w"),
        ("f58", "moCompRefPlane_c"),
        ("f58", "moUnitComponent_c"),
        ("owner", "moPart_c"),
    ):
        Reference = FieldsValue.get(SlotName)
        if not isinstance(
            Reference, ArchiveNode
        ) or Reference.ClassValue != RuntimeClass(ClassName, 1):
            raise BodyUnsupported(
                "linear pattern direction requires its local datum chain"
            )
        FieldsValue = Reference.FieldsValue


# the explicit datum validator belongs to the bounded ordinary pattern archive only
def CheckPatRule(
    ContextValue: BodyContext, ScopeValue: FieldScope, RuleValue: NativeField
) -> None:
    if (
        ContextValue.FlagsValue.get("part_local_pattern") != 1
        or RuleValue.NameValue != "OrdinaryPatternDatum"
    ):
        raise BodyUnsupported("unqualified native field validation")
    CheckPatDatum(ScopeValue)
