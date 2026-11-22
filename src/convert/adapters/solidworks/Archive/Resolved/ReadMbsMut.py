from collections.abc import MutableMapping

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# current part body mapping contributes a direct record only under its explicit manager context guard
def ReadMbsMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, OwnerValue: ArchiveNode
) -> MutableMapping[str, object] | None:
    if not (
        ContextValue.FlagsValue["model_is_part"]
        and ContextValue.FlagsValue["cmgr_f658"]
    ):
        return None
    FieldsValue: dict[str, object] = {}
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(FieldsValue),
        OwnerValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadSchemaMut(FrameValue, "moPartConfiguration_c.SerializeMBSMDataObjects")
    return FieldsValue
