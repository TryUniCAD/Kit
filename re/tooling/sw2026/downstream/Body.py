from functools import partial
from collections.abc import Mapping, Sequence

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


ROOT = RuntimeClass("moDownstreamIdData_c", 1)
UNIQUE = RuntimeClass("uniqueIdInfo_c", 1)
DOWNSTREAM_CONTEXT = "serializing_downstream_id_data"
IDENTITY_TABLES = ("f340", "f380", "f3c0", "f400", "f440")
TABLE_KINDS = {
    "f40": "moEntityIdRep_c",
    "f48": "moCompFace_c",
    "f60": "moCompEdge_c",
    "f78": "moCompVertex_c",
    "f100": "moCompFace_c",
    "f180": "moCompEdge_c",
    "f200": "moCompVertex_c",
    "f90": "moCompSolidBody_c",
    "fa8": "moCompSurfaceBody_c",
    "f280": "moCompSolidBody_c",
    "f300": "moCompSurfaceBody_c",
}


def scalar(name, kind):
    return NativeField("Scalar", name, kind)


def collection(name, *fields):
    return NativeField("Array", name, "i32", fields)


def pointers(name, *, key=False, identifier=None):
    fields = []
    if key:
        fields.append(scalar("key", "i32"))
    fields.append(NativeField("Node", "object", TABLE_KINDS[name]))
    if identifier:
        fields.append(scalar("word", identifier))
    return collection(name, *fields)


def identities(name, key_kind):
    return collection(
        name,
        scalar("key", key_kind),
        NativeField(
            "Branch", "key", ModeValue="Nonzero",
            BodyValue=(NativeField("Node", "object", UNIQUE.NameValue),),
        ),
    )


PREFIX = ("f08", "f0c", "f10", "f14", "f18", "f1c", "f20", "f28")
DIRECT = (
    *(scalar(field, "u32") for field in PREFIX),
    pointers("f40"),
    pointers("f48", identifier="u32"),
    pointers("f60", identifier="u32"),
    pointers("f78", identifier="u32"),
    identities("f340", "u32"),
    identities("f380", "i32"),
    identities("f3c0", "i32"),
    collection("f540", scalar("member", "i32")),
    pointers("f100", key=True, identifier="i32"),
    pointers("f180", key=True, identifier="i32"),
    pointers("f200", key=True, identifier="i32"),
    pointers("f90", identifier="i32"),
    pointers("fa8", identifier="i32"),
    identities("f400", "i32"),
    identities("f440", "i32"),
    pointers("f280", key=True, identifier="i32"),
    pointers("f300", key=True, identifier="i32"),
    NativeField("Text", "f30"),
    scalar("f38_high", "u32"),
    scalar("f38_low", "u32"),
    collection("f650", scalar("key", "i32"), *(scalar(axis, "f64") for axis in "xyz")),
)
LAYOUTS = {
    ROOT.NameValue: DIRECT,
    UNIQUE.NameValue: (
        *(scalar(field, "i32") for field in ("f08", "f0c", "f10")),
        scalar("high", "u32"), scalar("low", "u32"),
    ),
}
COLLECTIONS = tuple(field for field in DIRECT if field.KindValue == "Array")
ROOT_FIELDS = frozenset(field.NameValue for field in DIRECT)
COUNT_FIELDS = frozenset(field.NameValue + "#count" for field in COLLECTIONS)
UNIQUE_FIELDS = frozenset(field.NameValue for field in LAYOUTS[UNIQUE.NameValue])


def validate_body(node, entity_representations):
    names = node.FieldsValue.keys() - COUNT_FIELDS
    if names != ROOT_FIELDS:
        raise ValueError("downstream direct body contains missing or unknown fields")
    for field in COLLECTIONS:
        rows = node.FieldsValue[field.NameValue]
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
            raise ValueError(f"{field.NameValue} requires ordered native rows")
        expected = {rule.NameValue for rule in field.BodyValue if rule.KindValue != "Branch"}
        for row in rows:
            fields = expected
            if field.NameValue in IDENTITY_TABLES and isinstance(row, Mapping) and row.get("key"):
                fields = expected | {"object"}
            if not isinstance(row, Mapping) or row.keys() != fields:
                raise ValueError(f"{field.NameValue} row has missing or unknown fields")
    for section, expected in TABLE_KINDS.items():
        allowed = entity_representations if section == "f40" else (expected,)
        for row in node.FieldsValue[section]:
            value = row["object"]
            if value is not None and (type(value) is not ArchiveNode or value.ClassValue.NameValue not in allowed):
                raise ValueError(f"{section} requires its actual {expected} object")
    for section in IDENTITY_TABLES:
        for row in node.FieldsValue[section]:
            value = row.get("object")
            if bool(row["key"]) != (value is not None) or (
                value is not None and (type(value) is not ArchiveNode or value.ClassValue != UNIQUE
                                      or value.FieldsValue.keys() != UNIQUE_FIELDS)
            ):
                raise ValueError(f"{section} has inconsistent key and unique-info presence")


def require_standalone_context(context):
    flags = context.FlagsValue
    if (context.VersionValue != 19000 or flags.get(DOWNSTREAM_CONTEXT) != 1
            or flags.get("conditions", 0) or flags.get("adding_new_config", 0)):
        raise ValueError("direct downstream body requires the ordinary 19000 standalone context")
    if any(context.LayoutsValue.get(name) != fields for name, fields in LAYOUTS.items()):
        raise ValueError("downstream body requires its exact direct and unique-info layouts")


def read_standalone_body(raw, context, *, entity_representations=()):
    require_standalone_context(context)
    reader = GraphReader(BinaryReader(raw), ArchiveMaps(1), partial(ReadBodyMut, context))
    root = ArchiveNode(ROOT, {})
    ReadBodyMut(context, reader, root)
    if reader.Cursor.GetRemaining():
        raise ValueError("direct downstream body contains trailing bytes")
    validate_body(root, entity_representations)
    return root, reader.MapValue.Snapshot()


def write_standalone_body(root, context, *, entity_representations=()):
    require_standalone_context(context)
    if root.ClassValue != ROOT:
        raise ValueError("standalone downstream emission requires its concrete direct body")
    validate_body(root, entity_representations)
    writer = BodyWriter(ArchiveMaps(1), context, WriteBodyMut)
    WriteBodyMut(writer, root)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def isolated_body_context():
    return BodyContext(
        19000, LAYOUTS, {}, {name: (1,) for name in LAYOUTS},
        FlagsValue={DOWNSTREAM_CONTEXT: 1},
    )
