from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# concrete wrong classes wrong sketches and mismatched group selections must never acquire typed driver semantics
def AlterDimOwner(
    SketchValue: ArchiveNode, OtherSketch: ArchiveNode, ModeValue: str
) -> None:
    FieldsValue = CastValue(
        MutableMapping[str, object], SketchValue.FieldsValue["dims"]
    )
    DriverValue = ArchiveNode.RequireNode(NativeRows(FieldsValue["val_g2"])[0]["d"])
    DisplayList = ArchiveNode.RequireNode(FieldsValue["f118"])
    DisplayValue = ArchiveNode.RequireNode(
        NativeRows(DisplayList.FieldsValue["items"])[0]["o"]
    )
    HandleValue = ArchiveNode.RequireNode(
        NativeRows(DisplayValue.FieldsValue["f850"])[0]["o"]
    )
    if ModeValue == "wrong-handle-class":
        PointHandle = ArchiveNode.RequireNode(DriverValue.FieldsValue["h1"])
        PointHandle.ClassValue = RuntimeClass("sgLineHandle", 1)
    elif ModeValue == "wrong-value-index":
        HandleValue.FieldsValue["ff8"] = 1
    elif ModeValue == "wrong-sketch":
        HandleValue.FieldsValue["ff0"] = OtherSketch
    elif ModeValue == "missing-axis":
        FieldsValue["log_g1"] = NativeRows(FieldsValue["log_g1"])[:-1]
        FieldsValue["nlog1"] = 3
    elif ModeValue == "wrong-axis":
        LogicalValue = CastValue(
            MutableMapping[str, object], NativeRows(FieldsValue["log_g1"])[0]["d"]
        )
        LogicalValue["f80"] = 17
    elif ModeValue == "alternate-value":
        ArchiveNode.RequireNode(DriverValue.FieldsValue["f28"]).FieldsValue.update(
            {"f68": 1, "f60": 0.03125}
        )
    else:
        raise ValueError("unknown rectangle dimension ownership mutation")
