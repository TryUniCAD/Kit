from functools import partial

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField as Field
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
COORDINATES = (
    Field("Scalar", "u", "f64"), Field("Scalar", "v", "f64"),
    Field("Embed", "f20", "mgPoint_c.restore"),
)
ANGLE_CLASSES = {
    ANGLE_PLANE: (
        Field("Base", "moRefPlnData_c.serializePlaneData"), Field("Node", "f88", INTERFACE),
        Field("Scalar", "f148", "i32"), Field("Node", "f150", "moDisplayAngularDim_c"),
    ),
    INTERFACE: (Field("Node", "f08", ANGLE), Field("Node", "f10", COINCIDENT), Field("Node", "f18", COINCIDENT)),
    ANGLE: (Field("Node", "f08", "moPlaneRef_w"), *COORDINATES, Field("Scalar", "f38", "f64"), Field("Scalar", "f40", "u8")),
    COINCIDENT: (Field("Mask", "constraint_hinge", BodyValue=(Field("Node", "f08", "moLineRef_w"),), MaskValue=1), *COORDINATES),
    "moCompRefAxis_c": (Field("Base", "moCompFeature_c"), Field("Node", "ff8", "moRefGeom_c")),
}


def context(seed, link, *, source_replay=False):
    local = hinge_context(seed, link, disclosed_prefix=source_replay)
    if set(ANGLE_CLASSES) & local.LayoutsValue.keys():
        raise ValueError("shared angle grammar changed since the disclosed write boundary")
    wrapper_head, *wrapper_tail = local.LayoutsValue["moRefWrapper_c"]
    if wrapper_head.NameValue != "pattern_datum" or wrapper_head.ModeValue != "Context":
        raise ValueError("existing reference-wrapper roles changed since the disclosed angle boundary")
    bounded_wrapper = (
        Field("Branch", "constraint_hinge", BodyValue=(Field("Node", "f58", "moCompRefAxis_c"),),
              OtherValue=(wrapper_head,), ModeValue="Context"), *wrapper_tail,
    )
    local.LayoutsValue = {**local.LayoutsValue, **ANGLE_CLASSES, "moRefWrapper_c": bounded_wrapper}
    local.SchemasValue = {**local.SchemasValue, **dict.fromkeys(ANGLE_CLASSES, (1,))}
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
