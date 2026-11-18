from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.CheckOriginPose import (
    CheckOriginPose,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.CheckOriginNode import (
    CheckOriginNode,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.FindOriginNode import (
    FindOriginNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# external origin geometry must bind an actual same model component and selected origin rather than its cached label or zero coordinates
def ReadOriginRef(
    ExternalValue: ArchiveNode, ProfileValue: ArchiveNode, LinkValue: NativeLink
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode, ArchiveNode]:
    Wrapper = RequireNative(ExternalValue.FieldsValue.get("f08"), "moSketchExtRef_w")
    Selection = RequireNative(Wrapper.FieldsValue.get("f58"), "moCompSketchEntHandle_c")
    Component = RequireNative(Selection.FieldsValue.get("f58"), "moUnitComponent_c")
    KeyValue = NativeRecord(Selection.FieldsValue.get("ff0"))
    StampValue = KeyValue.get("f08")
    if (
        Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or Component.FieldsValue.get("has_ext") != 0
        or type(StampValue) is not int
        or StampValue < 0
        or any(
            Wrapper.FieldsValue.get(NameValue) != 0
            for NameValue in (
                "has_f10",
                "has_f18",
                "f68",
                "f6c",
                "f20",
                "f34",
                "f30",
                "f98",
                "fb0",
            )
        )
        or Wrapper.FieldsValue.get("f60") is not None
        or any(
            ExternalValue.FieldsValue.get(NameValue) is not None
            for NameValue in ("f10", "f18", "f20")
        )
    ):
        raise ValueError("typed origin reference has foreign or transformed ownership")
    OriginValue = FindOriginNode(LinkValue, KeyValue.get("f00"))
    CheckOriginNode(OriginValue, Selection)
    CheckOriginPose(ProfileValue, OriginValue, LinkValue.ConfigValue.RootValue)
    BackupValue = RequireNative(Wrapper.FieldsValue.get("fb8"), "moPointBackedUpData_c")
    Position = NativeRecord(BackupValue.FieldsValue.get("f08"))
    if any(Position.get(NameValue) != 0.0 for NameValue in ("x", "y", "z")):
        raise ValueError("typed origin reference has a nonorigin backup point")
    return OriginValue, Selection, Wrapper, BackupValue
