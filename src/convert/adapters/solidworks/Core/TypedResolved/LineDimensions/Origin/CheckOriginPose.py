from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a zero local datum denotes the model origin only in the actual untransformed matching principal profile frame
def CheckOriginPose(
    ProfileValue: ArchiveNode, OriginValue: ArchiveNode, ModelValue: ArchiveNode
) -> None:
    FrameValue = NativeRecord(ProfileValue.FieldsValue.get("pd_ff0"))
    OriginFrame = NativeRecord(OriginValue.FieldsValue.get("pd_ff0"))
    SupportValue = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    Component = RequireNative(SupportValue.FieldsValue.get("f58"), "moUnitComponent_c")
    if (
        FrameValue != OriginFrame
        or FrameValue.get("has_matrix") != 0
        or any(FrameValue.get(NameValue) != 0.0 for NameValue in ("f58", "f60", "f68"))
        or FrameValue.get("f70") != 1.0
        or FrameValue.get("f78") != 0
        or SupportValue.FieldsValue.get("f100") != 3
        or Component.FieldsValue.get("owner") is not ModelValue
        or Component.FieldsValue.get("has_ext") != 0
    ):
        raise ValueError("typed origin relation requires the matching Front frame")
