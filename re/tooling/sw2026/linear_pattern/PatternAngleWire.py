from functools import partial

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnglePlaneFields import KAnglePlaneFields
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.ReadMbsMut import ReadMbsMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar

from PatternHingeWire import context as hinge_context


ANGLE_PLANE = "moConstraintCoincLineAtAnglePlaneRefplaneData_c"
INTERFACE = "moConstraintRefplaneInterfaceData_c"
ANGLE = "moRefPlaneAngleGeom_c"
COINCIDENT = "moRefPlaneCoincidentGeom_c"


def context(seed, link, *, source_replay=False):
    local = hinge_context(seed, link, disclosed_prefix=source_replay)
    if any(local.LayoutsValue.get(name) != layout or local.SchemasValue.get(name) != (1,)
           for name, layout in KAnglePlaneFields.items()):
        raise ValueError("shared angle grammar differs from the measured constrained plane owners")
    wrapper, *_ = local.LayoutsValue["moRefWrapper_c"]
    if wrapper.NameValue != "constraint_hinge" or wrapper.ModeValue != "Context":
        raise ValueError("shared wrapper grammar lacks the measured hinge role")
    return local


def write_resolved(roots, extra, seed, link, *, source_replay=False):
    values = context(seed, link, source_replay=source_replay)
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), values, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(seed.CounterValue, "u32"))
    writer.OutputValue.extend(EncodeCount(len(roots)))
    for root in roots:
        WriteNodeMut(writer, root)
    WriteMbsMut(writer, FindModelRoot(seed), extra)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def read_resolved(raw, seed, link, *, source_replay=False):
    values = context(seed, link, source_replay=source_replay)
    cursor = BinaryReader(raw)
    if cursor.ReadUnsigned(4) != seed.CounterValue:
        raise ValueError("angled datum lost its complete configuration map")
    count, cursor.OffsetValue = ReadCount(cursor.BytesValue, cursor.OffsetValue)
    if not 0 < count <= 100:
        raise ValueError("angled datum root inventory is outside its bounded domain")
    reader = GraphReader(cursor, ArchiveMaps(seed.CounterValue, seed), partial(ReadBodyMut, values))
    roots = tuple(ReadNodeMut(reader) for _ in range(count))
    extra = ReadMbsMut(values, reader, FindModelRoot(seed))
    if cursor.GetRemaining():
        raise ValueError("unexpected tail after constrained angle research roots")
    return roots, extra, reader.MapValue.Snapshot()
