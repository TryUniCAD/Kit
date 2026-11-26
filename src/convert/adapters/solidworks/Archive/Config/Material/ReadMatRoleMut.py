from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KDensityClass,
    KMaterialClass,
)
from convert.adapters.solidworks.Archive.Config.Material.ReadMatBodyMut import (
    ReadMatBodyMut,
)
from convert.adapters.solidworks.Archive.Config.Material.RequireMatNode import (
    RequireMatNode,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# positional part roles share the physical cursor and preserve their new map owners
def ReadMatRoleMut(
    Cursor: BinaryReader,
    MapValue: ArchiveMaps,
    ContextValue: BodyContext,
    RootClass: RuntimeClass,
    *,
    AllowNull: bool = False,
) -> ArchiveNode | None:
    FirstSlot = MapValue.CounterValue
    ReaderValue = GraphReader(
        Cursor, MapValue, PartialValue(ReadMatBodyMut, ContextValue, RootClass)
    )
    NodeValue = ReadNodeMut(ReaderValue)
    if NodeValue is None and AllowNull:
        return None
    OwnerValue = RequireMatNode(NodeValue, MapValue, RootClass, FirstSlot)
    if RootClass == KMaterialClass:
        _ = RequireMatNode(
            OwnerValue.FieldsValue["f08"], MapValue, KDensityClass, FirstSlot
        )
    return OwnerValue
