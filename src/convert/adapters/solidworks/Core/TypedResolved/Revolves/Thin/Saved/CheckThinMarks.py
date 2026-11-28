from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the active and predecessor kernel marks belong to the actual operation and configuration model
def CheckThinMarks(
    RootValue: ArchiveNode, FeatureValue: ArchiveNode, MarksValue: tuple[int, int]
) -> None:
    ContextMark = RequireNative(RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c")
    FeatureMark = RequireNative(FeatureValue.FieldsValue.get("f3d0"), "moPMarkRecord_c")
    if MarksValue != (
        FeatureMark.FieldsValue.get("f18"),
        ContextMark.FieldsValue.get("f18"),
    ):
        raise ValueError(
            "SOLIDWORKS saved thin kernel rollback marks differ from their archive owners"
        )
