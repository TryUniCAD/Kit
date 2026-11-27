from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# omitted or extra inline mapping records would corrupt the resolved stream boundary
def WriteMbsMut(
    WriterValue: BodyWriter,
    OwnerValue: ArchiveNode,
    FieldsValue: MutableMapping[str, object] | None,
) -> None:
    FlagsValue = WriterValue.ContextValue.FlagsValue
    IsPresent = bool(FlagsValue["model_is_part"] and FlagsValue["cmgr_f658"])
    if IsPresent != (FieldsValue is not None):
        raise ValueError(
            "resolved inline body mapping does not match the manager context"
        )
    if FieldsValue is not None:
        FrameValue = WriteFrame(
            WriterValue,
            FieldScope(FieldsValue),
            OwnerValue,
            WriteSchemaMut,
            WriteFieldsMut,
        )
        WriteSchemaMut(FrameValue, "moPartConfiguration_c.SerializeMBSMDataObjects")
