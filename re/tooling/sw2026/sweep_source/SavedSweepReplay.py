from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from struct import pack
import sys

from convert.Geometry.Parasolid import EncodePartData, KTerminalFinSchema, ParaStream
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField as Field
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import WriteXmtEndMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import KLocalDescription, KLocalShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwFrame import ReadSwFrame
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KConfigStream, KResolvedFeaturesStream
from SavedSweepOwners import manager_owner, semantic_owners

MODEL_HEADER = KConfigStream + "-ModelHeader"
CMGR = "Contents/CMgr"
HISTORY = "moHistoryFeatItemData_c"
SIDE = "moSweepSideSurfIdRep_c"
DISPLAY = "moDisplayItem_c.Serialize"
BODY = "sweep.embeddedSection19000"
MBS = "moPartConfiguration_c.SerializeMBSMDataObjects"
FLAGS = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 1}
READER = import_module("convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut")
WRITER = import_module("convert.adapters.solidworks.Archive.Resolved.WriteResolMut")
MAKE_CONTEXT = READER.MakeResolvedCtx
READ_BODY = READER.ReadBodyMut
WRITE_BODY = WRITER.WriteBodyMut


def demand(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(raw):
    return sha256(raw).hexdigest()


def saved_context(version, seed, flags, usage):
    demand(version == 19000 and flags == FLAGS, "unexpected saved sweep archive context")
    context = MAKE_CONTEXT(version, seed, flags | {"cmgr_f658": 0}, usage)
    READER.UseSweepCtxMut(context)
    context.FlagsValue = dict(flags)
    context.LayoutsValue = context.LayoutsValue | {
        HISTORY: (Field("Base", "moNode_c"), Field("Node", "f48", "moCompFeature_c")),
        SIDE: (Field("Base", "er.FUN_4bba8790"), Field("Scalar", "f38", "i32"), Field("Scalar", "f3c", "i32")),
        MBS: (Field("Array", "fcd8", "u32", BodyValue=(Field("Scalar", "key", "i32"), Field("Node", "o")),
                    CountValue="n"),),
        DISPLAY: tuple(replace(item, BodyValue=(Field("Scalar", "v", "i32"),))
                       if item.NameValue == "f2b0" else item for item in context.LayoutsValue[DISPLAY]),
    }
    context.SchemasValue = context.SchemasValue | {HISTORY: (1,), "moCompFeature_c": (1,), SIDE: (1,)}
    context.VirtualValue = context.VirtualValue | {
        (HISTORY, 1000): None, (HISTORY, 1016): True,
        (HISTORY, 1208): "moNode_c.SerializeLWData", (HISTORY, 1216): None,
        ("moCompFeature_c", 1208): None, ("moCompFeature_c", 1216): None,
    }
    return context


def encode_sheet(rows):
    wire = bytearray(pack(">HI", 239, 0))
    seen = set()
    for row in rows:
        WriteXmtNodeMut(wire, row, KLocalShapes[row.KindValue], seen)
    WriteXmtEndMut(wire)
    return ParaStream(bytes(wire), KTerminalFinSchema, KLocalDescription)


def read_schema(frame, name):
    if name != BODY:
        ReadSchemaMut(frame, name)
        return
    cursor = frame.ReaderValue.Cursor
    start = cursor.GetOffset()
    demand(cursor.ReadUnsigned(1) == 0, "missing saved section")
    extent = cursor.ReadUnsigned(4)
    demand(cursor.ReadUnsigned(1) == 0 and 1 < extent <= min(32768, cursor.GetRemaining() + 1),
           "unsupported saved section extent or kernel flag")
    compressed = cursor.TakeBytes(extent - 1)
    payload = ReadSwFrame(compressed)
    rows = tuple(ReadActiveNodes(payload, Description=KLocalDescription.decode("ascii")).values())
    root, *others = rows
    demand((root.KindValue, root.IndexValue, root.Integer("owner"), root.Integer("next")) == (12, 1, 0, 2)
           and len(rows) == 10 and all(row.IndexValue != 2 for row in others),
           "wrong typed saved section body or nonresident sibling")
    demand(encode_sheet(rows) == payload and EncodePartData(payload) == compressed,
           "typed saved section changed its raw or compressed frame")
    frame.ScopeValue.FieldsValue.update(
        resident_nodes=rows, span=(start, cursor.GetOffset()), payload_sha256=digest(payload))


def write_schema(frame, name):
    if name != BODY:
        WriteSchemaMut(frame, name)
        return
    rows = frame.ScopeValue.FieldsValue["resident_nodes"]
    compressed = EncodePartData(encode_sheet(rows))
    frame.WriterValue.OutputValue.extend(pack("<BiB", 0, len(compressed) + 1, 0) + compressed)


def read_body(context, reader, node, *, SchemaReader=None):
    demand(SchemaReader is None, "saved replay entered the cold schema dispatcher")
    READ_BODY(context, reader, node, SchemaReader=read_schema)


def write_body(writer, node):
    WRITE_BODY(writer, node, SchemaWriter=write_schema)


def guard_runtime():
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    attempts = []

    def audit(event, _):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.system",
                     "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            attempts.append(event)
            raise RuntimeError(f"saved sweep replay attempted runtime access: {event}")

    sys.addaudithook(audit)
    return attempts


def inspect(raw, job):
    attempts = guard_runtime()
    READER.MakeResolvedCtx, READER.ReadBodyMut = saved_context, read_body
    WRITER.MakeResolvedCtx, WRITER.WriteBodyMut = saved_context, write_body
    archive = SldprtArchive.from_bytes(raw)
    demand((archive.format_version, ContainerMo(archive.streams)) == (4, 19000), "wrong archive profile")
    native_header = archive.require(MODEL_HEADER)
    header = ReadHeaderGraph(native_header, 19000)
    native_cfg = archive.require(KConfigStream)
    config = ReadConfigMut(native_cfg, 19000, header, SweepGhosts=True)
    config_bytes, config_again = WriteConfigMut(config.RootValue, 19000, header, SweepGhosts=True)
    native_mgr = archive.require(CMGR)
    manager = ReadCmgrMut(native_mgr, 19000)
    manager_bytes = WriteCmgrMut(manager.RootValue, 19000)
    actual_context = MakeLinkContext(config, manager)
    native_res = archive.require(KResolvedFeaturesStream)
    resolved = READER.ReadResolvedMut(native_res, 19000, config.MapValue, actual_context)
    resolved_bytes, resolved_again = WRITER.WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, 19000, config_again.MapValue, actual_context)
    demand(config_again.MapValue == config.MapValue and resolved_again.MapValue == resolved.MapValue
           and config.MapValue.CounterValue == resolved.MapBase == 110
           and resolved.MapValue.CounterValue == 278 and len(resolved.RootsValue) == 20,
           "saved sweep linked map altered during typed replay")
    for graph in (manager, config, resolved, config_again, resolved_again):
        demand(graph.ReportValue["completed"] and not graph.ReportValue["missing_schemas"]
               and not graph.ReportValue["provisional_schemas"], "unfinished saved sweep codec graph")
    demand(resolved.ExtraFields == {"n": 0, "fcd8": []}, "unexpected populated manager suffix")
    pairs = {MODEL_HEADER: (native_header, WriteHeadGraph(header, 19000)),
             KConfigStream: (native_cfg, config_bytes), CMGR: (native_mgr, manager_bytes),
             KResolvedFeaturesStream: (native_res, resolved_bytes)}
    streams = {}
    for name, (original, replay) in pairs.items():
        demand(original == replay, f"exact typed replay differs for {name}")
        streams[name] = {"bytes": len(original), "sha256": digest(original)}
    for name, expected in job["older_stream_digests"].items():
        demand(streams[name]["sha256"] == expected, "previous exact disclosed replay differs")
    info = semantic_owners(archive, config, manager, resolved, job["drivers_m"])
    manager_info = manager_owner(manager, manager_bytes, info["atom"]["id"])
    demand(not attempts and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "saved sweep replay used outside input")
    return {**job, "streams": streams, "maps": {"manager": 19, "config": 110, "resolved": 278},
            "runtime_accesses": len(attempts), "manager": manager_info, **info}
