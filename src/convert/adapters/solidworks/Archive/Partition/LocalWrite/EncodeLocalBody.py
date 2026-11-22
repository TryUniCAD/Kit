from struct import pack as PackValue

from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import (
    EncodeLocalXmt,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalBodyOwner import (
    LocalBodyOwner,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString


# a local feature group derives its wide key and record length from the typed body
def EncodeLocalBody(
    KeyValue: str,
    NodeValues: tuple[XmtNode, ...],
    *,
    OwnerValue: LocalBodyOwner | None = None,
) -> bytes:
    if type(KeyValue) is not str or not KeyValue or not KeyValue.isprintable():
        raise ValueError("local body requires a printable feature storage key")
    if OwnerValue is not None and (
        type(OwnerValue) is not LocalBodyOwner or OwnerValue.FeatureName != KeyValue
    ):
        raise ValueError("local body attributes require the actual feature storage key")
    PayloadValue = EncodePartData(EncodeLocalXmt(NodeValues, OwnerValue=OwnerValue))
    RecordSize = len(PayloadValue) + 1
    if RecordSize >= 1 << 31:
        raise ValueError("local body record length exceeds its signed archive word")
    return b"".join(
        (
            PackValue("<I", 1),
            EncodeString(CStringValue(KeyValue, True)),
            PackValue("<IIIBIB", 0, 1, 0, 0, RecordSize, 0),
            PayloadValue,
        )
    )
