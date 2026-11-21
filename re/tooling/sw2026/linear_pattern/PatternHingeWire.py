from functools import partial

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import KRefWrapperTailFields
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
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


AXIS_CLASSES = {
    "moRefAxis_c": (
        Field("Base", "moRefGeom_c"), Field("Node", "f700", "moPlaneInterAxisData_c"),
    ),
    "moPlaneInterAxisData_c": (
        Field("Embed", "f18", "mgPoint_c.restore"), Field("Embed", "f30", "mgPoint_c.restore"),
        Field("Scalar", "f08", "f64"), Field("Scalar", "f10", "f64"),
        Field("Embed", "f50", "mgVector_c.restore"), Field("Embed", "f68", "mgPoint_c.restore"),
        Field("Node", "f80", "moPlaneRef_w"), Field("Node", "f88", "moPlaneRef_w"),
    ),
    "moPlaneRef_w": (
        Field("Node", "f58", "moCompRefPlane_c"), *KRefWrapperTailFields,
        *(Field("Scalar", key, "f64") for key in ("fb0", "fb8", "fc0", "fc8")),
        Field("Embed", "fd0", "mgPoint_c.restore"), Field("Embed", "fe8", "mgVector_c.restore"),
        Field("Embed", "f100", "mgXform_c.restore"), Field("Embed", "f188", "mgPoint_c.restore"),
    ),
}
AXIS_VIRTUALS = {
    ("moRefAxis_c", 1000): "moFeature_c.SerializeXmlData",
    ("moRefAxis_c", 1016): True,
    ("moRefAxis_c", 1208): "moConcept_c.SerializeLWData",
    ("moRefAxis_c", 1216): "moConcept_c.SerializeResolvedData",
}


def context(seed, link, *, disclosed_prefix=False):
    if link != {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": int(disclosed_prefix)}:
        raise ValueError("finite hinge study requires an ordinary part without a generated MBSM body map")
    local = MakeResolvedCtx(19000, seed, link, None)
    if set(AXIS_CLASSES) & local.LayoutsValue.keys() or set(AXIS_VIRTUALS) & local.VirtualValue.keys():
        raise ValueError("already admitted native axis grammar needs independent review")
    local.LayoutsValue = {**local.LayoutsValue, **AXIS_CLASSES}
    local.SchemasValue = {**local.SchemasValue, **dict.fromkeys(AXIS_CLASSES, (1,))}
    local.VirtualValue = {**local.VirtualValue, **AXIS_VIRTUALS}
    return local


def write_roots(roots, seed, link, *, disclosed_prefix=False):
    values = context(seed, link, disclosed_prefix=disclosed_prefix)
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), values, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(seed.CounterValue, "u32"))
    writer.OutputValue.extend(EncodeCount(len(roots)))
    for root in roots:
        WriteNodeMut(writer, root)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def read_axis_stream(raw, seed, link, *, disclosed_prefix=False):
    values = context(seed, link, disclosed_prefix=disclosed_prefix)
    cursor = BinaryReader(raw)
    if cursor.ReadUnsigned(4) != seed.CounterValue:
        raise ValueError("finite hinge part lost its complete configuration map")
    count, cursor.OffsetValue = ReadCount(cursor.BytesValue, cursor.OffsetValue)
    if not 0 < count <= 100:
        raise ValueError("finite hinge research root inventory is outside its bounded domain")
    reader = GraphReader(cursor, ArchiveMaps(seed.CounterValue, seed), partial(ReadBodyMut, values))
    roots = []
    for _ in range(count):
        node = ReadNodeMut(reader)
        roots.append(node)
        if disclosed_prefix and node is not None and node.ClassValue.NameValue == "moRefAxis_c":
            return tuple(roots), reader.MapValue.Snapshot(), cursor.OffsetValue
    if disclosed_prefix or cursor.GetRemaining():
        raise ValueError("unexpected count or tail after finite hinge research roots")
    return roots, reader.MapValue.Snapshot()
