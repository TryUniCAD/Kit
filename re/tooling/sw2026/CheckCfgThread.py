from argparse import ArgumentParser
from codecs import lookup
import json
from pathlib import Path
from struct import pack, unpack
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, refuse, require
from CheckCfgOwners import MANIFEST as EARLIER_OWNERS, ROLES as EARLIER_ROLES, audit_run, load_case
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import KPMarkClass, KThreadMgrClass
from convert.adapters.solidworks.Archive.Config.Members.ReadCfgMember import ReadCfgMember
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigThreadSource01.json"
ROLES = {**EARLIER_ROLES, "fe38": KPMarkClass, "f12d0": KThreadMgrClass}


def load_controls(name):
    manifest = json.loads(MANIFEST.read_bytes())
    require(digest(EARLIER_OWNERS.read_bytes()) == manifest["earlier_owner_manifest_sha256"]
            and manifest["stream"] == "Contents/Config-0" and manifest["archive_version"] == 19000,
            "earlier owner manifest or archive binding changed")
    config, earlier, previous = load_case(name)
    control = manifest["controls"][name]
    require(all(earlier[key] == control[key] for key in ("path", "part_sha256", "config_sha256")),
            "the two owner manifests bind different controls")
    block, exploded = earlier["owners"]
    return config, (block, *control["owners"], exploded), previous


def read_member(config, owner, previous):
    start, end = owner["interval"]
    data = config[start:end]
    require(digest(data) == owner["sha256"], "native member extent or hash differs")
    role = ROLES[owner["field"]]
    seed = MapSnapshot(owner["counter"][0], previous.EntriesValue)
    graph = ReadCfgMember(data, 19000, seed, role)
    entries = graph.MapValue.EntriesValue
    initial = seed.EntriesValue
    require(all(left is right for left, right in zip(entries[:len(initial)], initial, strict=True))
            and graph.MapValue.CounterValue == owner["counter"][1]
            and graph.ReportValue["completed"], "member changed inherited map entries or the native counter")
    node = graph.RootValue
    if node is None:
        require(owner["object_slot"] is None and entries == initial, "native null owner changed the map")
    else:
        class_entry, node_entry = entries[len(initial):]
        require(node.ClassValue == role and node.StartOffset == 0 and node.EndOffset == len(data)
                and node.IndexValue == node_entry.IndexValue == owner["object_slot"]
                and node_entry.EntryValue is node and class_entry.EntryValue is node.ClassValue
                and class_entry.IndexValue == owner["new_class_slot"], "concrete member lost its record identity")
    return data, graph, seed


def native_summary(config, owner, entry):
    data, graph, seed = entry
    node = graph.RootValue
    indices = {"class_slot": owner["new_class_slot"], "object_slot": owner["object_slot"]}
    result = {"field": owner["field"], "bytes": len(data), "counter": owner["counter"], **indices,
              "class": None if node is None else [node.ClassValue.NameValue, node.ClassValue.SchemaValue],
              "inherited": [item.IndexValue for item in seed.EntriesValue]}
    if owner["field"] == "fe38":
        start, end = owner["mark_wire"]
        mark, = unpack("<i", config[start:end])
        require(mark == owner["mark_id"] and node.FieldsValue == {"f18": mark}, "mark word moved")
        result["mark_id"] = mark
    if owner["field"] == "f12d0":
        result["boolean_calls"] = graph.ReportValue["field_calls"].get("Boolean", 0)
        if node is not None:
            start, end = owner["boolean_wire"]
            wire = config[start:end]
            count_start, count_end = owner["count_wire"]
            require(digest(wire) == owner["boolean_wire_sha256"]
                    and unpack("<i", config[count_start:count_end]) == (0,), "thread word or count moved")
            value, = unpack("<i", wire)
            require(node.FieldsValue == {"n": 0, "f18": [], "f1a0#wire": value, "f1a0": int(value != 0)},
                    "thread member did not retain both word identities")
            result.update(raw_word=node.FieldsValue["f1a0#wire"], runtime_boolean=node.FieldsValue["f1a0"])
    return result


def authored_contrast(thread):
    _data, graph, _seed = thread
    seed = graph.MapValue
    slot = next(entry.IndexValue for entry in seed.EntriesValue if entry.EntryValue == KThreadMgrClass)
    tag = 0x8000 | slot
    values = []
    for word in (-2147483648, 0, 7, 2147483647):
        data = pack("<Hii", tag, 0, word)
        new = ReadCfgMember(data, 19000, seed, KThreadMgrClass)
        entries = new.MapValue.EntriesValue
        node = new.RootValue
        require(all(left is right for left, right in zip(entries[:-1], seed.EntriesValue, strict=True))
                and entries[-1].EntryValue is node and node.IndexValue == seed.CounterValue
                and node.StartOffset == 0 and node.EndOffset == len(data)
                and new.MapValue.CounterValue == seed.CounterValue + 1
                and node.ClassValue is next(entry.EntryValue for entry in seed.EntriesValue if entry.IndexValue == slot),
                "the inherited descriptor did not allocate exactly one new thread manager")
        require(node.FieldsValue == {"n": 0, "f18": [], "f1a0#wire": word, "f1a0": int(word != 0)},
                "authored signed boolean word was discarded")
        values.append([node.FieldsValue["f1a0#wire"], node.FieldsValue["f1a0"]])
    return tag, values


def ladder_refusals(mark, thread, tag):
    mark_data, mark_graph, mark_seed = mark
    data, graph, seed = thread
    role = KThreadMgrClass
    mark_index = mark_graph.RootValue.IndexValue
    return [
        refuse("truncated_mark", mark_data[:-1], mark_seed, KPMarkClass, "truncated SOLIDWORKS archive field"),
        refuse("null_mark", b"\0\0", mark_seed, KPMarkClass, "partition mark member requires its concrete root"),
        refuse("truncated_boolean", data[:-1], seed, role, "truncated SOLIDWORKS archive field"),
        refuse("trailing", data + b"\0", seed, role, "trailing data"),
        refuse("wrong_archive_version", data, seed, role, "archive version 19000", 18900),
        refuse("wrong_role", data, seed, KPMarkClass, "unsupported body owner"),
        refuse("wrong_schema", data[:2] + b"\0\0" + data[4:], seed, role, "unsupported body owner"),
        refuse("reused_thread", pack("<H", graph.RootValue.IndexValue), graph.MapValue, role, "new root object"),
        refuse("missing_class", pack("<Hii", tag, 0, 0), seed, role, "archive class reference"),
        refuse("negative_map_count", pack("<Hii", tag, -1, 0), graph.MapValue, role, "populated SOLIDWORKS thread"),
        refuse("populated_holder", pack("<HiiIHi", tag, 1, 81, 1, mark_index, -9),
               graph.MapValue, role, "populated SOLIDWORKS thread"),
    ]


def run(name):
    config, owners, previous = load_controls(name)
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    entries = {}
    for owner in owners:
        record = read_member(config, owner, previous)
        entries[owner["field"]] = record
        previous = record[1].MapValue
    mark, thread = entries["fe38"], entries["f12d0"]
    rows = [native_summary(config, owner, entry) for owner, entry in zip(owners[1:3], (mark, thread), strict=True)]
    report = {"members": rows, "final_counter": previous.CounterValue,
              "final_slots": [entry.IndexValue for entry in previous.EntriesValue],
              "runtime_external_accesses": 0, "authored_boolean_pairs": [], "refusals": []}
    if name == "ladder":
        tag, values = authored_contrast(thread)
        report.update(authored_boolean_pairs=values, refusals=ladder_refusals(mark, thread, tag))
    return report


def main():
    parser = ArgumentParser(description="Verify the physical configuration mark and thread owners")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
