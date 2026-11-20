from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields,
    KExtTailFields,
    KRefCfgFields,
    KSharedFields,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderWire import StoreFieldsMut
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore


# embedded file definitions preserve typed fields between the owning object fields
def RequireFieldMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise ValueError("SOLIDWORKS header requires a typed embedded field mapping")
    return CastValue(Mapping[str, object], Value)


# an ordinary file definition writes shared identity before its configuration suffix
def StoreFileMut(
    Buffer: bytearray, WriterValue: ObjectStore, Fields: Mapping[str, object]
) -> None:
    StoreFieldsMut(
        Buffer, WriterValue, KSharedFields, RequireFieldMap(Fields["shared"])
    )
    StoreFieldsMut(Buffer, WriterValue, KExtLeadFields, Fields)
    StoreFieldsMut(
        Buffer, WriterValue, KRefCfgFields, RequireFieldMap(Fields["refcfg"])
    )
    StoreFieldsMut(Buffer, WriterValue, KExtTailFields, Fields)
