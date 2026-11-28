from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)


# axis geometry must belong to the actual selected local sketch rather than a matching cached line
def ReadRevAxisRef(
    NodeValue: ArchiveNode, ProfileValue: ArchiveNode, RootValue: ArchiveNode
) -> AxisReference:
    WrapperValue = RequireNative(NodeValue.FieldsValue.get("f830"), "moLineRef_w")
    FieldsValue = WrapperValue.FieldsValue
    SelectedValue = RequireNative(FieldsValue.get("f58"), "moCompSketchEntHandle_c")
    SelectFields = SelectedValue.FieldsValue
    Component = RequireNative(SelectFields.get("f58"), "moUnitComponent_c")
    if (
        Component.FieldsValue.get("owner") is not RootValue
        or Component.FieldsValue.get("has_ext") != 0
        or (
            NativeRecord(SelectFields.get("ff0")).get("f00")
            != NativeNodeId(ProfileValue)
        )
        or FieldsValue.get("f60") is not None
        or any(FieldsValue.get(NameValue) != 0 for NameValue in ("has_f10", "has_f18"))
        or any(
            SelectFields.get(NameValue) != 0
            for NameValue in ("has_fb0", "has_fb8", "has_fc0", "has_fc8", "has_fd0")
        )
    ):
        raise ValueError(
            "ordinary revolve axis is outside its actual self component and profile"
        )
    HandleValue = RequireNative(SelectFields.get("f0f8"), "sgLineHandle")
    MarkValue = SelectFields.get("f100")
    if type(MarkValue) is not int or MarkValue <= 0:
        raise ValueError(
            "ordinary revolve selected axis has no positive permanent mark"
        )
    return AxisReference(
        WrapperValue,
        SelectedValue,
        HandleValue,
        ReadDimHandle(HandleValue, "sgLineHandle"),
        MarkValue,
    )
