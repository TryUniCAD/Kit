from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from struct import pack, unpack
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import KAtomClass, KPartClass
from convert.adapters.solidworks.Archive.Config.Atoms.MakeAtomCtx import MakeAtomCtx
from convert.adapters.solidworks.Archive.Config.Atoms.ReadAtomMgr import ReadAtomMgr
from convert.adapters.solidworks.Archive.Config.Atoms.ReadAtomNodeMut import ReadAtomNodeMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigAtomSource01.json"


class RootDescriptor(Exception):
    def __init__(self, node):
        super().__init__()
        self.node = node


def load_case(name):
    manifest = json.loads(MANIFEST.read_bytes())
    case = manifest["controls"][name]
    content = (ROOT / case["path"]).read_bytes()
    require(digest(content) == case["part_sha256"], "native atom input changed")
    archive = SldprtArchive.from_bytes(content)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == manifest["archive_version"] == 19000,
            "unexpected native atom archive version")
    streams = {key: archive.require(label) for key, label in manifest["stream_names"].items()}
    for key, stream in streams.items():
        assert case["streams"][key] == {"bytes": len(stream), "sha256": digest(stream)}
    return streams, version, case


def root_descriptor(_reader, node):
    raise RootDescriptor(node)


def seed_manager(streams, version, case):
    config = streams["config"]
    cursor = BinaryReader(config)
    mapped = ArchiveMaps(1)
    try:
        ReadNodeMut(GraphReader(cursor, mapped, root_descriptor))
    except RootDescriptor as observed:
        model = observed.node
    else:
        raise AssertionError("the native root descriptor was not visited")
    assert cursor.GetOffset() == 14 and model.StartOffset == 0 and model.EndOffset is None
    assert not model.FieldsValue and model.ClassValue == KPartClass
    assert [row.IndexValue for row in mapped.Snapshot().EntriesValue] == case["root_slots"]
    assert mapped.EntryMap[model.IndexValue].EntryValue is model
    header = ReadHeaderGraph(streams["header"], version)
    anchors = HeaderRefNodes(header, version)
    assert len(anchors) == 1 and anchors[0].IndexValue == case["header_standalone_slot"]
    BindNodesMut(mapped, anchors)
    assert mapped.EntryMap[case["header_slot"]].EntryValue is anchors[0]
    assert mapped.BaseValue == case["native_base"]
    return model, MapSnapshot(case["counter"][0], mapped.Snapshot().EntriesValue)


def signed_at(data, interval):
    value, = unpack("<i", data[slice(*interval)])
    return value


def inspect_manager(streams, version, case, model, seed):
    config = streams["config"]
    info = case["manager"]
    start, end = info["interval"]
    data = config[start:end]
    assert digest(data) == info["sha256"]
    decoded = ReadAtomMgr(data, version, seed, model)
    assert decoded.ReportValue["completed"] and not model.FieldsValue
    assert decoded.ReportValue["field_calls"]["Normalize"] == 1
    fields = decoded.FieldsValue
    assert fields["f260"] == signed_at(config, (start, start + 4)) == info["f260"]
    assert fields["n6c"] == signed_at(config, (start + 4, start + 8)) == 1
    assert fields["fa8"] == unpack("<I", config[end - 4:end])[0] == info["fa8"]
    atom, = (row["o"] for row in fields["atoms"])
    check_atom(config, case["atom"], start, atom)
    entries = decoded.MapValue.EntriesValue
    inherited = seed.EntriesValue
    assert all(old is new for old, new in zip(inherited, entries[:-2], strict=True))
    assert [seed.CounterValue, decoded.MapValue.CounterValue] == info["counter"]
    assert entries[-2].EntryValue is atom.ClassValue and entries[-1].EntryValue is atom
    assert [entries[-2].IndexValue, entries[-1].IndexValue] == [
        case["atom"]["class_slot"], case["atom"]["object_slot"],
    ]
    return data, decoded, atom


def check_atom(config, info, start, atom):
    fields = atom.FieldsValue
    assert atom.ClassValue == KAtomClass and atom.IndexValue == info["object_slot"]
    physical_start, physical_end = info["interval"]
    assert atom.StartOffset == physical_start - start and atom.EndOffset == physical_end - start
    assert digest(config[physical_start:physical_end]) == info["sha256"]
    for field, interval in info["fields_spans"].items():
        if field == "f144":
            raw = unpack("<I", config[slice(*interval)])[0]
            assert fields["f144#wire"] == raw == info["wire_state"]
            assert fields["f144"] == info["state"]
        else:
            assert fields[field] == signed_at(config, interval)
    assert fields["f140"] == info["atom_id"] and fields["body_kind"] == info["body_kind"]
    projected = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
    assert digest(projected) == info["fields_sha256"]


def reject_link_body(_reader, _node):
    raise AssertionError("the feature output link opened a new body")


def inspect_producer(stream, info, graph, atom):
    tag = stream[slice(*info["link_span"])]
    assert digest(tag) == info["link_sha256"]
    cursor = BinaryReader(tag)
    maps = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    reference = ReadNodeMut(GraphReader(cursor, maps, reject_link_body))
    assert reference is atom and cursor.GetRemaining() == 0
    assert maps.Snapshot() == graph.MapValue
    feature_id = signed_at(stream, info["feature_id_span"])
    output_id = signed_at(stream, info["output_id_span"])
    assert feature_id == info["feature_id"] == atom.FieldsValue["f130"] == atom.FieldsValue["f12c"]
    assert output_id == atom.FieldsValue["f140"]
    return {"class": info["class"], "feature_slot": info["object_slot"],
            "feature_id": feature_id, "output_id": output_id, "reference_slot": reference.IndexValue}


def author_body(class_slot, atom_id, state, *, flags=0, body_kind=0, name_tag=0, tail=0):
    data = pack("<HHiIii", 0x8000 | class_slot, name_tag, -23, 0x40000004, -47, -9)
    data += b"\x03alt" + pack("<iHHi", 0, 0, 0, tail)
    data += pack("<iIiiIi", atom_id, state, -31, -41, 0xF0000060, body_kind)
    if body_kind:
        return data
    data += pack("<iii", -11, 1, -1)
    if not flags or flags & 0x400000:
        data += pack("<iii", -7, 1, -7)
    return data + pack("<i", 6)


def author_manager(values, *, count=None):
    n = len(values) if count is None else count
    return pack("<ii", 207, n) + b"".join(values) + pack("<I", 0xABCDEF01)


def state_values(node):
    data = node.FieldsValue
    return [data["f144#wire"], data["f144"], data["f140"], data["f130"], data["f12c"]]


def authored_context(seed, slot):
    raw = 0x80000003
    cases = []
    for flags in (0x80, 0x400080):
        context = MakeAtomCtx(19000)
        context.FlagsValue["conditions"] = flags
        data = author_body(slot, -19, raw, flags=flags)
        cursor = BinaryReader(data)
        mapped = ArchiveMaps(seed.CounterValue, seed)
        decoder = partial(ReadAtomNodeMut, context)
        body = ReadNodeMut(GraphReader(cursor, mapped, decoder))
        assert cursor.GetRemaining() == 0 and body.EndOffset == len(data)
        assert body.IndexValue == seed.CounterValue and mapped.EntryMap[body.IndexValue].EntryValue is body
        assert body.ClassValue is mapped.EntryMap[slot].EntryValue
        assert all(mapped.EntryMap[entry.IndexValue] is entry for entry in seed.EntriesValue)
        cases.append([flags, len(data), state_values(body), body.FieldsValue.get("f180")])
    return cases


def authored_rows(model, seed, slot):
    raw = 0x80000003
    data = author_manager((author_body(slot, -19, raw), author_body(slot, 207, 1)))
    decoded = ReadAtomMgr(data, 19000, seed, model)
    nodes = [row["o"] for row in decoded.FieldsValue["atoms"]]
    entries = decoded.MapValue.EntriesValue
    for node, entry in zip(nodes, entries[-2:], strict=True):
        assert entry.EntryValue is node and entry.IndexValue == node.IndexValue
        assert node.ClassValue is next(item.EntryValue for item in seed.EntriesValue if item.IndexValue == slot)
    assert all(left is right for left, right in zip(entries[:-2], seed.EntriesValue, strict=True))
    assert decoded.ReportValue["completed"]
    return {"counter": [seed.CounterValue, decoded.MapValue.CounterValue],
            "slots": [node.IndexValue for node in nodes], "values": [state_values(node) for node in nodes],
            "manager_tail": decoded.FieldsValue["fa8"], "names": [node.FieldsValue["f20"] for node in nodes]}


def refuse(label, data, seed, model, expected, version=19000):
    try:
        ReadAtomMgr(data, version, seed, model)
    except ValueError as error:
        require(expected in str(error), f"{label} produced a different rejection: {error}")
        return label
    raise AssertionError(f"{label} admitted an out of scope atom manager")


def authored_refusals(model, seed, slot, original, anchor):
    body = author_body(slot, -19, 3)
    valid = author_manager((body,))
    wrong = b"moAtom_c"
    wrong_class = pack("<HHH", 0xFFFF, 2, len(wrong)) + wrong
    return [
        refuse("truncated", valid[:-1], seed, model, "truncated SOLIDWORKS archive field"),
        refuse("trailing", valid + b"\0", seed, model, "trailing data"),
        refuse("wrong_version", valid, seed, model, "archive version 19000", 18900),
        refuse("detached_part", valid, seed, ArchiveNode(KPartClass, {}), "requires its mapped part owner"),
        refuse("wrong_schema", author_manager((wrong_class,)), seed, model, "unsupported SOLIDWORKS atom body owner"),
        refuse("null_atom", author_manager((b"\0\0",)), seed, model, "requires concrete atoms"),
        refuse("borrowed_atom", author_manager((pack("<H", original),)), seed, model, "requires newly read atoms"),
        refuse("duplicate_ids", author_manager((body, body)), seed, model, "duplicate SOLIDWORKS manager atom identifier"),
        refuse("negative_count", author_manager((), count=-1), seed, model, "unqualified SOLIDWORKS atom manager count"),
        refuse("named_owner", author_manager((author_body(slot, -19, 3, name_tag=anchor),)),
               seed, model, "unqualified SOLIDWORKS atom concept links"),
        refuse("list_tail", author_manager((author_body(slot, -19, 3, tail=-1),)),
               seed, model, "unqualified SOLIDWORKS atom resolved list"),
        *[refuse(f"body_kind_{kind}", author_manager((author_body(slot, -19, 3, body_kind=kind),)),
                 seed, model, "unsupported native field path SOLIDWORKS atom body kind")
          for kind in (-1, 1, 2)],
    ]


def run(name):
    streams, version, case = load_case(name)
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    model, seed = seed_manager(streams, version, case["manager"])
    _data, manager, atom = inspect_manager(streams, version, case, model, seed)
    link = inspect_producer(streams["resolved"], case["producer"], manager, atom)
    output = {"interval": case["manager"]["interval"], "counter": case["manager"]["counter"],
              "original_entry_count": case["manager"]["original_entry_count"],
              "inherited_slots": [entry.IndexValue for entry in seed.EntriesValue],
              "header_standalone_slot": case["manager"]["header_standalone_slot"],
              "atom": state_values(atom), "body_kind": atom.FieldsValue["body_kind"], "producer": link,
              "atom_slot": atom.IndexValue, "body_stamps": [atom.FieldsValue[key] for key in ("f180", "f1b0")],
              "runtime_external_accesses": 0}
    if name == "ladder":
        inherited = manager.MapValue
        class_slot = case["atom"]["class_slot"]
        output.update(authored=authored_rows(model, inherited, class_slot),
                      context=authored_context(inherited, class_slot),
                      refusals=authored_refusals(model, inherited, class_slot, atom.IndexValue, case["manager"]["header_slot"]))
    return output


def main():
    parser = ArgumentParser(description="Verify the ordinary configuration atom manager and linked output identity")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
