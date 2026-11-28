from ProjectD01Concentric import require

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Config.Units.ReadUnitTable import ReadUnitTable
from convert.adapters.solidworks.Archive.Config.Units.UnitLayouts import KUnitLayouts
from convert.adapters.solidworks.Archive.Config.Units.UnitSchemas import KUnitSchemas, KUnitTableClass
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import ReadUnitNodes


UNIT_STREAM = "Contents/User Units Table"


def encode_table(table):
    require(table.ClassValue == KUnitTableClass, "user units require their actual typed table")
    context = BodyContext(19000, KUnitLayouts, {}, KUnitSchemas)
    writer = BodyWriter(ArchiveMaps(1), context, WriteBodyMut)
    WriteNodeMut(writer, table)
    return bytes(writer.OutputValue), writer.MapValue.CounterValue


def verify_unit_table(root, payload):
    require(root.ClassValue == RuntimeClass("moAssembly_c", 1) and root.FieldsValue["f9c0"] is None,
            "standalone units require their own assembly model and absent analysis table")
    units = ReadUnitNodes(root)
    graph = ReadUnitTable(payload, 19000, MapSnapshot(1, ()))
    stored, stored_counter = encode_table(graph.RootValue)
    expected, expected_counter = encode_table(root.FieldsValue["f9b8"])
    require(graph.ReportValue["completed"] and graph.MapValue.CounterValue == stored_counter == expected_counter
            and stored == payload == expected,
            "standalone user units differ from their embedded model table or canonical archive map")
    return units, stored_counter


def add_unit_stream(streams, state):
    require(UNIT_STREAM not in streams, "assembly user units already have an emitted scope")
    root = state.RootValue
    payload, counter = encode_table(root.FieldsValue["f9b8"])
    _, read_counter = verify_unit_table(root, payload)
    require(counter == read_counter, "standalone unit map counter differs from its actual emitted graph")
    return streams | {UNIT_STREAM: payload}
