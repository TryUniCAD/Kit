from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadArrayMut import ReadArrayMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import WriteArrayMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteValueMut import WriteValueMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalRef import ExternalRef
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut

DEPTH_FIELDS = (NativeField("Node", "next"), NativeField("Node", "terminal"))
DEPTH_ROWS = NativeField(
    "Array", "links", "Count", BodyValue=(NativeField("Node", "link"),)
)
PROBE_FIELDS = {
    "ValueRoot": (
        NativeField("Scalar", "number#0", "i32", OtherName="number"),
        NativeField("Text", "label"),
        NativeField("Array", "rows", "Count", BodyValue=(NativeField("Node", "link"),)),
    ),
    "ValueChild": (NativeField("Text", "label"), NativeField("Node", "owner")),
    "Depth": DEPTH_FIELDS,
    "ExtraDepth": DEPTH_FIELDS,
    "RowDepth": (DEPTH_ROWS,),
    "ExtraRowDepth": (DEPTH_ROWS,),
}


def set_depth_links(node, child, counted):
    if counted:
        node.FieldsValue["links"] = [{"link": child}, {"link": None}]
    else:
        node.FieldsValue.update(next=child, terminal=None)


def make_depth(depth, new_terminal_class, counted):
    class_name = "RowDepth" if counted else "Depth"
    root = ArchiveNode(RuntimeClass(class_name, 1), {})
    node = root
    for index in range(1, depth):
        name = (
            f"Extra{class_name}"
            if new_terminal_class and index == depth - 1
            else class_name
        )
        child = ArchiveNode(RuntimeClass(name, 1), {})
        set_depth_links(node, child, counted)
        node = child
    set_depth_links(node, root, counted)
    return root


def make_graph(source, inherited):
    if inherited is not None:
        return ArchiveNode(
            RuntimeClass("ValueChild", 1),
            {"label": source["label"], "owner": inherited},
        )
    if "depth" in source:
        return make_depth(
            source["depth"],
            source.get("new_terminal_class", False),
            source.get("counted", False),
        )
    label = source["label"]
    if isinstance(label, list):
        label = tuple(label)
    root = ArchiveNode(
        RuntimeClass(source.get("class", "ValueRoot"), 1),
        {"number": source["number"], "label": label},
    )
    child = ArchiveNode(
        RuntimeClass("ValueChild", 1), {"label": source["child_label"], "owner": root}
    )
    root.FieldsValue["rows"] = [{"link": child}, {"link": child}, {"link": None}]
    return root


def reject_schema(*args):
    raise ValueError("the synthetic body values contain no nested schemas")


def archive_state(writer):
    maps = writer.MapValue
    return (
        bytes(writer.OutputValue),
        maps.Snapshot(),
        dict(maps.ClassLookup),
        dict(maps.ObjectLookup),
        writer.NestingDepth,
    )


def write_counted_overflow(frame, rule, node):
    writer = frame.WriterValue
    if writer.NestingDepth != 128 or node.ClassValue in writer.MapValue.ClassLookup:
        raise ValueError("counted overflow requires a new class at depth 128")
    before = archive_state(writer)
    try:
        WriteValueMut(frame, rule)
    except ValueError as error:
        if archive_state(writer) != before:
            raise ValueError(
                "counted overflow changed output or archive slots"
            ) from error
        raise ValueError(f"{error}; archive state intact") from None


def write_fields(frame, fields):
    for rule in fields:
        value = frame.ScopeValue.FieldsValue.get(rule.NameValue)
        if (
            isinstance(value, ArchiveNode)
            and value.ClassValue.NameValue == "ExtraRowDepth"
        ):
            write_counted_overflow(frame, rule, value)
            continue
        apply_field = WriteArrayMut if rule.KindValue == "Array" else WriteValueMut
        apply_field(frame, rule)


def write_body(writer, node):
    frame = WriteFrame(
        writer, FieldScope(node.FieldsValue), node, reject_schema, write_fields
    )
    write_fields(frame, PROBE_FIELDS[node.ClassValue.NameValue])


def write_document(source, maps, inherited):
    writer = BodyWriter(maps, BodyContext(19000, {}, {}, {}), write_body)
    try:
        WriteNodeMut(writer, make_graph(source, inherited))
    except ValueError as error:
        if writer.NestingDepth:
            raise ValueError("body writer depth was not restored") from error
        if source.get("class") == "" and (
            writer.OutputValue or writer.MapValue.CounterValue != 1
        ):
            raise ValueError("empty descriptor consumed archive state") from error
        raise
    if writer.NestingDepth:
        raise ValueError("body writer depth was not restored")
    return bytes(writer.OutputValue)


def read_text(frame, rule):
    cursor = frame.ReaderValue.Cursor
    start = cursor.OffsetValue
    fields = dict(frame.ScopeValue.FieldsValue)
    try:
        ReadValueMut(frame, rule)
    except ValueError as error:
        intact = cursor.OffsetValue == start and frame.ScopeValue.FieldsValue == fields
        raise ValueError(
            f"{error}; text checkpoint {start}, cursor {cursor.OffsetValue}, fields intact {intact}"
        ) from None


def read_fields(frame, fields):
    for rule in fields:
        if rule.KindValue == "Array":
            ReadArrayMut(frame, rule)
        elif rule.KindValue == "Text":
            read_text(frame, rule)
        else:
            ReadValueMut(frame, rule)


def read_graph(payload, maps):
    context = BodyContext(19000, {}, {}, {})

    def read_body(reader, node):
        frame = ReadFrame(
            context, reader, FieldScope(node.FieldsValue), node, reject_schema, read_fields
        )
        class_name = node.ClassValue.NameValue
        if class_name in ("RowDepth", "ExtraRowDepth"):
            ReadArrayMut(frame, DEPTH_ROWS)
        else:
            read_fields(frame, PROBE_FIELDS[class_name])

    cursor = BinaryReader(payload)
    reader = GraphReader(cursor, maps, read_body)
    root = ReadNodeMut(reader)
    if root is None or cursor.GetRemaining() or reader.NestingDepth:
        raise ValueError("synthetic body values need one complete root graph")
    return root


def describe_depth(root):
    counted = root.ClassValue.NameValue == "RowDepth"
    node = root
    for depth in range(1, 129):
        fields = node.FieldsValue
        if node.IndexValue != depth + 1:
            raise ValueError("depth control lost an allocated object")
        if counted:
            if fields["links#count"] != 2:
                raise ValueError("depth control lost an inline count")
            child, terminal = (row["link"] for row in fields["links"])
        else:
            child, terminal = fields["next"], fields["terminal"]
        if terminal is not None:
            raise ValueError("depth control lost its null terminal")
        if child is root:
            return {"depth": depth, "terminal_index": child.IndexValue}
        node = ArchiveNode.RequireNode(child)
    raise ValueError("depth control lost its root backreference")


def describe_graph(root):
    if root.ClassValue.NameValue in ("Depth", "RowDepth"):
        return describe_depth(root)
    fields = root.FieldsValue
    child, alias, terminal = (row["link"] for row in fields["rows"])
    child = ArchiveNode.RequireNode(child)
    if (
        child is not alias
        or terminal is not None
        or child.FieldsValue["owner"] is not root
    ):
        raise ValueError("synthetic body values lost a shared reference")
    return {
        "number": fields["number#0"],
        "label": fields["label"],
        "child_label": child.FieldsValue["label"],
        "row_count": fields["rows#count"],
        "root_index": root.IndexValue,
        "child_index": child.IndexValue,
    }


def load_seed(path, sparse):
    if path is None:
        return ArchiveMaps(1), None
    primary = ArchiveMaps(1)
    root = read_graph(path.read_bytes(), primary)
    inherited = ArchiveNode.RequireNode(root.FieldsValue["rows"][0]["link"])
    snapshot = primary.Snapshot()
    if sparse:
        index = inherited.IndexValue
        snapshot = MapSnapshot(
            snapshot.CounterValue,
            tuple(entry for entry in snapshot.EntriesValue if entry.IndexValue != index),
        )
        inherited = ExternalRef(index)
    return ArchiveMaps(snapshot.CounterValue, snapshot), inherited


def describe_link(root, inherited, maps):
    if (
        root.FieldsValue["owner"] is not inherited
        or root.ClassValue is not inherited.ClassValue
    ):
        raise ValueError("linked body lost its seeded object or class identity")
    return {
        "label": root.FieldsValue["label"],
        "inherited_index": inherited.IndexValue,
        "root_index": root.IndexValue,
        "base": maps.BaseValue,
        "next": maps.CounterValue,
    }


def main():
    parser = ArgumentParser(description="Check independently authored body field graphs")
    parser.add_argument("mode", choices=("read", "write"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed-primary", type=Path)
    parser.add_argument("--sparse-seed", action="store_true")
    options = parser.parse_args()
    if options.sparse_seed and options.seed_primary is None:
        parser.error("a sparse seed requires a primary stream")
    maps, inherited = load_seed(options.seed_primary, options.sparse_seed)
    if options.mode == "write":
        source = loads(options.source.read_text(encoding="utf-8"))
        payload = write_document(source, maps, inherited)
    else:
        root = read_graph(options.source.read_bytes(), maps)
        report = (
            describe_graph(root)
            if inherited is None
            else describe_link(root, inherited, maps)
        )
        payload = dumps(report).encode("utf-8")
    with options.output.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
