from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# native marks must bind the actual selected partition and originating activation across both streams
def CheckBodyMarks(
    LinkValue: NativeLink, BossValue: ArchiveNode, Marks: tuple[int, int]
) -> None:
    Selected = RequireNative(BossValue.FieldsValue.get("f3d0"), "moPMarkRecord_c")
    Activation = RequireNative(
        LinkValue.ConfigValue.RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c"
    )
    if (Selected.FieldsValue.get("f18"), Activation.FieldsValue.get("f18")) != Marks:
        raise ValueError(
            "SOLIDWORKS attached circle marks disagree with native history"
        )
