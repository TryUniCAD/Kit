from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# reference variants isolate wrong model feature point and backup ownership after normal archive decoding
def AlterRefMut(
    SketchValue: ArchiveNode, OtherSketch: ArchiveNode, ModeValue: str
) -> None:
    PointValue = NativeRecord(NativeRows(SketchValue.FieldsValue["points"])[4]["point"])
    ExternalValue = ArchiveNode.RequireNode(PointValue["ext"])
    WrapperValue = ArchiveNode.RequireNode(ExternalValue.FieldsValue["f08"])
    Selection = ArchiveNode.RequireNode(WrapperValue.FieldsValue["f58"])
    if ModeValue == "missing-origin":
        FeatureKey = CastValue(
            MutableMapping[str, object], Selection.FieldsValue["ff0"]
        )
        FeatureKey["f00"] = 987654
    elif ModeValue == "foreign-owner":
        Component = ArchiveNode.RequireNode(Selection.FieldsValue["f58"])
        Component.FieldsValue["owner"] = OtherSketch
    elif ModeValue == "point-mark":
        Selection.FieldsValue["f100"] = 2
    elif ModeValue == "selected-index":
        ArchiveNode.RequireNode(Selection.FieldsValue["f0f8"]).FieldsValue["idx"] = 1
    elif ModeValue == "reference-mode":
        WrapperValue.FieldsValue["f68"] = 1
    elif ModeValue == "backup-position":
        Backup = ArchiveNode.RequireNode(WrapperValue.FieldsValue["fb8"])
        Position = CastValue(MutableMapping[str, object], Backup.FieldsValue["f08"])
        Position["x"] = 0.000125
    else:
        raise ValueError("unknown origin graph mutation")
