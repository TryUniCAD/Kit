from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# unfamiliar modes and secondary selectors stay outside the measured ordinary edge profile
def CheckChmfMode(NodeValue: ArchiveNode) -> None:
    FieldsValue = RequireNative(NodeValue, "Chamfer_c").FieldsValue
    if (
        any(
            FieldsValue.get(FieldName) != Expected
            for FieldName, Expected in (
                ("f860", 0),
                ("f8a0", 10),
                ("f878", 0),
                ("f8c0", 1),
                ("f87c", 0),
                ("has_f808", 0),
                ("f8f0", 1),
            )
        )
        or any(
            NativeRows(
                RequireNative(FieldsValue.get(FieldName), "suObList").FieldsValue[
                    "items"
                ]
            )
            for FieldName in ("f890", "f898")
        )
        or any(
            FieldsValue[FieldName] is not None
            for FieldName in (
                "f820",
                "f8b0",
                "f8b8",
                "f828",
                "f830",
                "f838",
                "f840",
                "f848",
                "f850",
                "f858",
            )
        )
    ):
        raise ValueError("unsupported ordinary SOLIDWORKS chamfer mode or selector")
