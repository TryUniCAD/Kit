from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.ManagerFields import (
    KManagerFields,
    KManagerSchemas,
)
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# ordinary text admission must reject populated advanced owners before projecting optional xml values
def ReadPropManager(BufferValue: bytes, VersionValue: int) -> None:
    ContextValue = BodyContext(
        VersionValue,
        KManagerFields,
        {},
        KManagerSchemas,
        NewBodyUsage(VersionValue, None),
    )
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
    )
    RootValue = ReadNodeMut(ReaderValue)
    if RootValue is None or RootValue.ClassValue != RuntimeClass("moCusPropMgr_c", 1):
        raise ValueError("part properties require their actual native manager owner")
    if ReaderValue.Cursor.GetRemaining() != 0:
        raise ValueError("part property manager has unclassified trailing data")
    FieldsValue = RootValue.FieldsValue
    if (FieldsValue["f0c"], FieldsValue["f08"], FieldsValue["f54"]) != (-1, 0, 0):
        raise ValueError(
            "part property manager policy is outside the compatible profile"
        )
