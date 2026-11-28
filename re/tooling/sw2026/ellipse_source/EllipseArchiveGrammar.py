from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.EllipseFields import (
    KEllipseFields, KEllipseHandle as HANDLE, KEllipseLayout as INLINE,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

POINT = "sk.sgPoint.FUN_4c58f910"
POINT_INDEX_FIELDS = ("fdc", "fe0", "fe4", "fe8", "fec")
RESOLVED = import_module("convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut")
BODY = import_module("convert.adapters.solidworks.Archive.Bodies.ReadBodyMut")


def location(reader, node, usage):
    return {
        "offset": reader.Cursor.GetOffset(),
        "map_base": reader.MapValue.BaseValue,
        "map_before": reader.MapValue.CounterValue,
        "node_index": node.IndexValue,
        "field_path": list(usage.FieldPath),
        "schema_path": list(usage.SchemaPath),
    }


@contextmanager
def observe_link(mode):
    make_context, read_body, read_schema = RESOLVED.MakeResolvedCtx, RESOLVED.ReadBodyMut, BODY.ReadSchemaMut
    observed = {"handles": [], "inline": [], "points": []}

    def make_resolved_context(*args):
        context = make_context(*args)
        if mode == "handle":
            return replace(context, LayoutsValue=context.LayoutsValue | {HANDLE: KEllipseFields[HANDLE]},
                           SchemasValue=context.SchemasValue | {HANDLE: (1,)})
        return context

    def record_handle(context, reader, node):
        if node.ClassValue.NameValue != HANDLE:
            return read_body(context, reader, node)
        record = location(reader, node, context.UsageValue) | {
            "tag_start": node.StartOffset, "descriptor_schema": node.ClassValue.SchemaValue, "node": node}
        observed["handles"].append(record)
        try:
            return read_body(context, reader, node)
        finally:
            record.update(end=reader.Cursor.GetOffset(), map_after=reader.MapValue.CounterValue)

    def record_inline(frame, layout):
        if layout not in (INLINE, POINT):
            return read_schema(frame, layout)
        reader, node, usage = frame.ReaderValue, frame.NodeValue, frame.ContextValue.UsageValue
        record = location(reader, node, usage) | {"scope": frame.ScopeValue.FieldsValue, "node": node}
        observed["inline" if layout == INLINE else "points"].append(record)
        try:
            return read_schema(frame, layout)
        finally:
            record.update(end=reader.Cursor.GetOffset(), map_after=reader.MapValue.CounterValue)

    RESOLVED.MakeResolvedCtx, RESOLVED.ReadBodyMut, BODY.ReadSchemaMut = (
        make_resolved_context, record_handle, record_inline)
    try:
        yield observed
    finally:
        RESOLVED.MakeResolvedCtx, RESOLVED.ReadBodyMut, BODY.ReadSchemaMut = make_context, read_body, read_schema


def parse_link(archive):
    with observe_link("current") as observed:
        value = ReadNativeLink(archive, 0, ReadEllipses=True)
    return value, observed
