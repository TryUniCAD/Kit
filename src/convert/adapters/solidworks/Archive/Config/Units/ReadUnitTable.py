from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Units.CheckUnitRows import CheckUnitRows
from convert.adapters.solidworks.Archive.Config.Units.ReadUnitNodeMut import (
    ReadUnitNodeMut,
)
from convert.adapters.solidworks.Archive.Config.Units.UnitLayouts import KUnitLayouts
from convert.adapters.solidworks.Archive.Config.Units.UnitSchemas import (
    KUnitSchemas,
    KUnitTableClass,
)
from convert.adapters.solidworks.Archive.Config.Units.UnitTableGraph import (
    UnitTableGraph,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# a bounded native unit table must consume its complete record before publishing the new map
def ReadUnitTable(
    BufferValue: bytes, VersionValue: int, SeedValue: MapSnapshot
) -> UnitTableGraph:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported("SOLIDWORKS unit table requires archive version 19000")
    ContextValue = BodyContext(VersionValue, KUnitLayouts, {}, KUnitSchemas)
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue), MapValue, PartialValue(ReadUnitNodeMut, ContextValue)
    )
    RootValue = ReadNodeMut(ReaderValue)
    if (
        RootValue is None
        or RootValue.ClassValue != KUnitTableClass
        or ReaderValue.Cursor.GetRemaining()
    ):
        raise BodyUnsupported(
            "SOLIDWORKS unit table has an invalid root or trailing data"
        )
    IndexValue = ObjectIndex(MapValue, RootValue)
    if IndexValue is None or IndexValue < SeedValue.CounterValue:
        raise BodyUnsupported("SOLIDWORKS unit table requires a new root object")
    CheckUnitRows(RootValue, MapValue)
    ContextValue.UsageValue.IsComplete = True
    return UnitTableGraph(
        RootValue, MapValue.Snapshot(), GetBodyReport(ContextValue.UsageValue)
    )
