from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module

from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import KRefWrapperTailFields
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField as Field
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.CurveFields import KNoteCurveFields
from para.Partition import decode_active
from SweepModel import require

SWEEP = "moSweep_c"
SIDE = "moSweepSideSurfIdRep_c"
CURVE = "moGeneralCurveRef_w"
CONTACT = "moWireContact_c"
PROFILE = "moCompProfile_c"
DATA = "sweep.data19000"
BODY = "sweep.embeddedSection19000"
GUARD = "sweep.standard19000"
RESOLVED = import_module("convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut")
BODY_CODEC = import_module("convert.adapters.solidworks.Archive.Bodies.ReadBodyMut")


def scalars(fields):
    return tuple(Field("Scalar", name, kind) for name, kind in (row.split(":") for row in fields.split()))


def collections(names, layout="rf.suObArray"):
    return tuple(Field("Embed", name, layout) for name in names.split())


LAYOUTS = {
    SWEEP: (
        Field("Base", "moBodyFeature_c"),
        Field("Embed", "f820", DATA),
        Field("Base", GUARD),
        *scalars("fc0c:i32 fc10:u8 fc14:u8 fc18:u8 fc1c:u8 f80c:u8 fc20:u8 fc24:u8"),
    ),
    SIDE: (Field("Base", "er.FUN_4bba8790"), *scalars("f38:i32 f3c:i32")),
    DATA: (
        *collections("f2c0 f2e0 f300"),
        *scalars("f270:u8 f274:u8 f278:i32 f70:f64 f2ac:u8 f2b0:u8 f7c:i32 f80:i32"),
        Field("Base", "sweep.noTangency19000"),
        *collections("f98 fe0", "suObList"),
        *scalars("f230:i32 f78:u8 f234:u8 f238:f64 f240:f64 f248:i32 f24c:i32 f2b4:i32"),
        *scalars("f280:f64 f288:f64 f290:i32 f27c:u8 f2a8:u8 f258:i32 f260:f64"),
        Field("Node", "f298", "moTwistDataForBiDirectionalSweep_c"),
        Field("Node", "f2a0", "moEndPointRef_w"),
        *scalars("f2b8:u8"),
        *collections("f320 f340"),
        *scalars("f3b0:i32"),
    ),
    PROFILE: (Field("Base", "moCompFeature_c"),),
    CURVE: (
        Field("Node", "f58", PROFILE), *KRefWrapperTailFields,
        *scalars("fb0:f64 fb8:f64 has_fc8:u8"),
        Field("Branch", "has_fc8", BodyValue=(Field("Embed", "fc8", BODY),), ModeValue="Nonzero"),
        *KNoteCurveFields[CURVE][0].BodyValue[3:],
    ),
    CONTACT: (
        Field("Embed", "f50", "suObList"),
        *scalars("f90:f64 f98:i32"),
        Field("Node", "fa0", "moDisplayAngularDim_c"),
        *scalars("fa8:f64 fb0:i32 fb8:i32 fc8:i32 fcc:i32"),
        Field("Node", "fe0", "moLoftSynchRef_c"),
        *scalars("f40:u32 f44:u32 f48:u32 fc0:f64"),
        Field("Node", "fe8", CURVE),
    ),
}


def section_transport(cursor):
    start = cursor.GetOffset()
    require(cursor.ReadUnsigned(1) == 0, "curve present flag encloses absent kernel body")
    length = ReadScalarMut(cursor, "i32")
    kernel = cursor.ReadUnsigned(1)
    require(kernel == 0 and 1 < length <= cursor.GetRemaining() + 1,
            "section kernel frame does not match its declared boundary")
    data = cursor.TakeBytes(length - 1)
    payload, = DecodePartData(data, "sweep section")
    require(payload.wrapper_offset == 0 and payload.stored_size == len(data)
            and payload.schema == "SCH_3701250_37102_13006", "unknown section transmit wrapper")
    header = ParaHeaderData(payload.data)
    require(header is not None and header.description == ": TRANSMIT FILE created by modeller version 3701250",
            "unknown section transmit header")
    return {
        "span": [start, cursor.GetOffset()],
        "declared_body_bytes": length,
        "kernel_word": kernel,
        "transmit_schema": payload.schema,
        "transmit_sha256": payload.sha256,
        "uncompressed_bytes": payload.uncompressed_size,
        "nodes": decode_active(payload.data[header.body_offset:]),
    }


@contextmanager
def observe(mode):
    old_context = RESOLVED.MakeResolvedCtx
    old_body = RESOLVED.ReadBodyMut
    old_schema = BODY_CODEC.ReadSchemaMut
    events = {"refusals": [], "spans": {}}

    def context(*args):
        value = old_context(*args)
        if mode == "baseline":
            return value
        require(value.VersionValue == 19000 and value.FlagsValue == {
            "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 0 if mode == "cold" else 1,
        }, "sweep observation requires the measured ordinary 19000 part context")
        linked = mode in ("linked", "cold")
        layouts = LAYOUTS if linked else {SWEEP: LAYOUTS[SWEEP][:1]}
        registered = (SWEEP, SIDE, CURVE, CONTACT, PROFILE) if linked else (SWEEP,)
        return replace(
            value,
            LayoutsValue=value.LayoutsValue | layouts,
            SchemasValue=value.SchemasValue | {name: (1,) for name in registered},
            VirtualValue=value.VirtualValue | {
                (SWEEP, slot): value.VirtualValue["moICE_c", slot] for slot in (1000, 1016, 1208, 1216)
            },
        )

    def body(ctx, reader, node):
        start = reader.Cursor.GetOffset()
        try:
            return old_body(ctx, reader, node)
        except BodyUnsupported as error:
            if not events["refusals"]:
                events["refusals"].append({
                    "class": node.ClassValue.NameValue,
                    "schema": node.ClassValue.SchemaValue,
                    "tag_offset": node.StartOffset,
                    "body_offset": start,
                    "cursor": reader.Cursor.GetOffset(),
                    "object_slot": node.IndexValue,
                    "map_base": reader.MapValue.BaseValue,
                    "next_slot": reader.MapValue.CounterValue,
                    "field_path": list(ctx.UsageValue.FieldPath),
                    "diagnostic": str(error),
                })
            raise

    def schema(frame, name):
        fields = frame.ScopeValue.FieldsValue
        if name == BODY:
            fields.update(section_transport(frame.ReaderValue.Cursor))
            return
        if name == GUARD:
            embedded = fields["f820"]
            require(embedded["f234"] == embedded["f258"] == 0 and embedded["f278"] == 0,
                    "thin, circular-profile or alternate twist sweep")
            return
        if name == "sweep.noTangency19000":
            require(fields["f7c"] == fields["f80"] == 0, "alternate sweep tangency owners")
            return
        start = frame.ReaderValue.Cursor.GetOffset()
        old_schema(frame, name)
        if frame.NodeValue.ClassValue.NameValue == SWEEP and name in (DATA, "moBodyFeature_c"):
            require(name not in events["spans"], "repeated sweep inline owner")
            events["spans"][name] = [start, frame.ReaderValue.Cursor.GetOffset()]

    RESOLVED.MakeResolvedCtx, RESOLVED.ReadBodyMut, BODY_CODEC.ReadSchemaMut = context, body, schema
    try:
        yield events
    finally:
        RESOLVED.MakeResolvedCtx, RESOLVED.ReadBodyMut, BODY_CODEC.ReadSchemaMut = old_context, old_body, old_schema
