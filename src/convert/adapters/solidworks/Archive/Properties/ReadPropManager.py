from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut

# the compatible property owner has one concrete schema and an independent map
KPropManager = RuntimeClass("moCusPropMgr_c", 1)

# no keyed rows can be traversed in the compatible empty profile
KEmptyPropFields = (
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f08", "i32"),
    NativeField("Scalar", "n20", "u32"),
    NativeField("Scalar", "f54", "u8"),
)


# the binary manager must establish that xml has no competing property value owners
def ReadPropManager(BufferValue: bytes, VersionValue: int) -> None:
    if VersionValue != 19000:
        raise ValueError(
            "part property manager requires ordinary archive version 19000"
        )
    TypeName = KPropManager.NameValue
    ContextValue = BodyContext(
        VersionValue, {TypeName: KEmptyPropFields}, {}, {TypeName: (1,)}
    )
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
    )
    RootValue = ReadNodeMut(ReaderValue)
    if (
        RootValue is None
        or RootValue.ClassValue != KPropManager
        or ReaderValue.Cursor.GetRemaining()
        or tuple(RootValue.FieldsValue[Field.NameValue] for Field in KEmptyPropFields)
        != (-1, 0, 0, 0)
    ):
        raise ValueError("part properties require an empty compatible native manager")
