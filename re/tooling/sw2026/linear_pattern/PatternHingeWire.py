from functools import partial

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AxisFields import KAxisFields
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
    if (any(local.LayoutsValue.get(name) != layout or local.SchemasValue.get(name) != (1,)
            for name, layout in KAxisFields.items())
            or any(local.VirtualValue.get(owner) != target for owner, target in AXIS_VIRTUALS.items())):
        raise ValueError("shared native axis grammar differs from the measured hinge owners")
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
