from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# an inactive or alternative source origin relation cannot justify a fixed external datum in the public sketch
def AlterFixMut(SketchValue: ArchiveNode, ModeValue: str) -> None:
    Dimensions = NativeRecord(SketchValue.FieldsValue["dims"])
    RelationValue = CastValue(
        MutableMapping[str, object], NativeRows(Dimensions["log_g1"])[0]["d"]
    )
    RelationValue["f54" if ModeValue == "origin-suppressed" else "f90"] = 1
    SketchValue.FieldsValue["dims"] = Dimensions
