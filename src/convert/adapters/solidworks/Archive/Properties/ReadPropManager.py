from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.CheckEmptyProps import (
    CheckEmptyProps,
)
from convert.adapters.solidworks.Archive.Properties.MakePropContext import (
    MakePropContext,
)
from convert.adapters.solidworks.Archive.Properties.ManagerFields import (
    KManagerFields,
    KManagerSchemas,
)
from convert.adapters.solidworks.Archive.Properties.ReadPropNodeMut import (
    ReadPropNodeMut,
)
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut

# the compatible property owner has one concrete schema and an independent map
KPropManager = RuntimeClass("moCusPropMgr_c", 1)

# the legacy empty owner uses the same measured body layouts as the current manager
KPropertyLayoutVersion = 19000


# the binary manager must establish that xml has no competing property value owners
def ReadPropManager(BufferValue: bytes, VersionValue: int) -> None:
    if VersionValue not in (18000, 19000):
        raise ValueError("part property manager requires supported archive version")
    ContextValue = BodyContext(
        KPropertyLayoutVersion, KManagerFields, {}, KManagerSchemas
    )
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadPropNodeMut, ContextValue),
    )
    RootValue = ReadNodeMut(ReaderValue)
    if (
        RootValue is None
        or RootValue.ClassValue != KPropManager
        or ReaderValue.Cursor.GetRemaining()
    ):
        raise ValueError("part properties require an empty compatible native manager")
    if VersionValue == 18000:
        CheckEmptyProps(RootValue)
    elif tuple(
        RootValue.FieldsValue[NameValue] for NameValue in ("f0c", "f08", "n20", "f54")
    ) != (-1, 0, 0, 0):
        raise ValueError("part properties require an empty compatible native manager")


# the typed manager must consume its complete rooted stream with its independent archive map
def ReadPropRoot(BufferValue: bytes, VersionValue: int) -> ArchiveNode:
    ContextValue = MakePropContext(VersionValue)
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
    return RootValue
