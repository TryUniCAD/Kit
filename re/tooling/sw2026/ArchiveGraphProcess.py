from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag


def write_graph(root, maps):
    output = bytearray()

    def write_descriptor(descriptor):
        name = descriptor.NameValue.encode("ascii")
        output.extend(EncodeScalar(descriptor.SchemaValue, "u16"))
        output.extend(EncodeScalar(len(name), "u16"))
        output.extend(name)

    def write_body(node):
        output.extend(EncodeScalar(node.FieldsValue["value"], "i32"))
        links = node.FieldsValue["links"]
        output.extend(EncodeCount(len(links)))
        for link in links:
            WriteObjectMut(writer, link)

    writer = ObjectStore(
        maps, lambda tag: output.extend(EncodeTag(tag)), write_descriptor, write_body
    )
    WriteObjectMut(writer, root)
    return bytes(output)


def write_document(source):
    definitions = source["nodes"]
    nodes = {
        name: ArchiveNode(RuntimeClass(*row["class"]), {"value": row["value"]})
        for name, row in definitions.items()
    }
    for name, row in definitions.items():
        nodes[name].FieldsValue["links"] = [
            None if link is None else nodes[link] for link in row["links"]
        ]
    primary = ArchiveMaps(1)
    primary_bytes = write_graph(nodes[source["primary"]], primary)
    seed = primary.Snapshot()
    linked = ArchiveMaps(seed.CounterValue, seed)
    linked_bytes = EncodeScalar(seed.CounterValue, "u32") + write_graph(
        nodes[source["linked"]], linked
    )
    return primary_bytes, linked_bytes


def read_body(reader, node):
    cursor = reader.Cursor
    node.FieldsValue["value"] = ReadScalarMut(cursor, "i32")
    count = ReadCountMut(cursor, 2)
    node.FieldsValue["links"] = [ReadNodeMut(reader) for _ in range(count)]


def read_graph(cursor, maps, class_name):
    root = ReadTypedMut(GraphReader(cursor, maps, read_body), class_name)
    if cursor.GetRemaining():
        raise ValueError("synthetic archive graph retains unread bytes")
    return root


def describe_graph(primary, seed, linked, maps):
    for entry in seed.EntriesValue:
        if maps.EntryMap[entry.IndexValue] is not entry:
            raise ValueError("seeded archive slot changed identity")
    classes, nodes = [], []
    for index, row in maps.EntryMap.items():
        owner = row.EntryValue
        if isinstance(owner, RuntimeClass):
            classes.append([index, owner.NameValue, owner.SchemaValue])
        else:
            nodes.append((index, owner))
    slots = {id(owner): index for index, owner in nodes}
    return {
        "primary": {
            "root": slots[id(primary)],
            "next": seed.CounterValue,
            "slots": [entry.IndexValue for entry in seed.EntriesValue],
        },
        "linked": {
            "root": slots[id(linked)],
            "base": maps.BaseValue,
            "next": maps.CounterValue,
        },
        "classes": classes,
        "objects": [
            [
                index,
                owner.ClassValue.NameValue,
                owner.FieldsValue["value"],
                [
                    None if link is None else slots[id(link)]
                    for link in owner.FieldsValue["links"]
                ],
            ]
            for index, owner in nodes
        ],
    }


def read_document(primary_bytes, linked_bytes):
    primary = ArchiveMaps(1)
    root = read_graph(BinaryReader(primary_bytes), primary, "Root")
    seed = primary.Snapshot()
    cursor = BinaryReader(linked_bytes)
    base = ReadScalarMut(cursor, "u32")
    linked = ArchiveMaps(base, seed)
    child = read_graph(cursor, linked, "Leaf")
    return describe_graph(root, seed, child, linked)


def main():
    parser = ArgumentParser(description="Compare synthetic linked archive graphs")
    parser.add_argument("mode", choices=("write", "read"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    names = ("Primary.bin", "Linked.bin")
    if options.mode == "write":
        document = loads(options.source.read_text(encoding="utf-8"))
        for name, payload in zip(names, write_document(document), strict=True):
            with (options.output / name).open("xb") as stream:
                stream.write(payload)
    else:
        report = read_document(*[(options.source / name).read_bytes() for name in names])
        with options.output.open("x", encoding="utf-8") as stream:
            stream.write(dumps(report))


if __name__ == "__main__":
    main()
