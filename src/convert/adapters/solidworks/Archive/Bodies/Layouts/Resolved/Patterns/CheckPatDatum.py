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
