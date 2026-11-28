from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# the config owned manager needs one independent index row only for its measured empty placement shape
def AsmExplodeNode(
    RootValue: ArchiveNode, PublishedValues: tuple[ArchiveNode, ...]
) -> ArchiveNode | None:
    if any(
        NodeValue.ClassValue.NameValue == "moExplViewManager_c"
        for NodeValue in PublishedValues
    ):
        raise ValueError(
            "assembly exploded manager must belong only to its direct config owner"
        )
    ExplodedValue = RootValue.FieldsValue.get("f1590")
    if ExplodedValue is None:
        return None
    ManagerValue = RequireNode(ExplodedValue, "moExplViewManager_c")
    ClassValue = ManagerValue.ClassValue
    FieldsValue = ManagerValue.FieldsValue
    if (
        not isinstance(ClassValue, RuntimeClass)
        or ClassValue.SchemaValue != 1
        or FieldsValue.get("owner") is not RootValue
        or FieldInt(RootValue.FieldsValue, "f1598") != 0
        or FieldInt(FieldsValue, "f3a0") != -1
        or FieldInt(FieldsValue, "f3a4") != -1
        or type(FieldsValue.get("f398")) is not float
        or FieldsValue["f398"] != 0.0
        or any(
            NameValue not in FieldsValue or FieldsValue[NameValue] != EmptyValue
            for NameValue, EmptyValue in (
                ("f358", None),
                ("f360", None),
                ("f368", EmptyRootRows()),
                ("f60", {"list": {"n": 0, "items": list[object]()}, "tail": 0}),
            )
        )
    ):
        raise ValueError(
            "assembly keyword exploded manager has unsupported ownership or placement state"
        )
    return ManagerValue
