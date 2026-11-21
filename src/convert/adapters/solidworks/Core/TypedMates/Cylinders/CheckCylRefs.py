from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    ReadRows,
)


# detached support cylinders belong to the actual parent epoch and cannot borrow selected child ownership
def CheckCylRefs(
    NodeValue: ArchiveNode, ModelValue: ArchiveNode, HeaderValue: ArchiveNode
) -> None:
    for RowValue in ReadRows(NodeValue.FieldsValue.get("f3c8")):
        Support = RequireNode(RowValue.get("o"), "moCylinderRef_w")
        Component = RequireNode(Support.FieldsValue.get("f58"), "moCompRefCylinder_c")
        OwnerValue = RequireNode(Component.FieldsValue.get("f58"), "moUnitComponent_c")
        if (
            OwnerValue.FieldsValue.get("owner") is not ModelValue
            or FieldInt(OwnerValue.FieldsValue, "has_ext") != 0
            or (FieldInt(Support.FieldsValue, "f08") & 0xFFFFFFFF)
            != FieldInt(HeaderValue.FieldsValue, "f40")
            or FieldInt(Support.FieldsValue, "f0c") != 0
            or any(
                FieldInt(Support.FieldsValue, NameValue) != -12345
                for NameValue in ("f74", "f78", "f7c")
            )
        ):
            raise ValueError(
                "concentric detached support owner or parent epoch differs"
            )
