from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from struct import pack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from CheckCfgMembers import digest, originals, refuse, require
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KCfgMemberSchemas,
    KExplViewClass,
    KFeatColorClass,
    KSketchBlockClass,
)
from convert.adapters.solidworks.Archive.Config.Members.MemberLayouts import KMemberLayouts
from convert.adapters.solidworks.Archive.Config.Members.MemberVirtuals import KMemberVirtuals
from convert.adapters.solidworks.Archive.Config.Members.ReadCfgMember import ReadCfgMember
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigFieldActionsSource01.json"
ROLES = {"fe80": KSketchBlockClass, "f13f8": KExplViewClass}


def load_case(name):
    manifest = json.loads(MANIFEST.read_bytes())
    case = manifest["controls"][name]
    result, part_sha, config_sha = originals(name)
    data = (ROOT / case["path"]).read_bytes()
    require(digest(data) == part_sha == case["part_sha256"], "wrong native part")
    archive = SldprtArchive.from_bytes(data)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == manifest["archive_version"] == 19000,
            "wrong native archive version")
    config = archive.require(manifest["stream"])
    require(digest(config) == config_sha == case["config_sha256"], "wrong physical configuration")
    previous = result[-1][1].MapValue
    require(previous.CounterValue == case["owners"][0]["counter"][0], "native color handoff changed")
    return config, case, previous


def audit_run(event, _args):
    if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec",
                 "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen") or event.startswith("socket."):
        raise PermissionError("the native field executor attempted external access")


def inspect(graph, owner, data, seed):
    expected = owner["counter"]
    actual = graph.MapValue
    before = seed.EntriesValue
    require(actual.CounterValue == expected[1]
            and all(a is b for a, b in zip(actual.EntriesValue[:len(before)], before, strict=True))
            and graph.ReportValue["completed"], "the physical member and inherited map differ")
    node = graph.RootValue
    values = {"field": owner["field"], "counter": expected, "bytes": len(data),
              "sha256": digest(data), "inherited_map_slots": [row.IndexValue for row in before],
              "object_slot": None if node is None else node.IndexValue,
              "class_slot": None, "branch_calls": graph.ReportValue["field_calls"].get("Branch", 0),
              "virtual_calls": graph.ReportValue["field_calls"].get("Virtual", 0)}
    if node is None:
        require(owner["object_slot"] is None and actual.EntriesValue == before, "a null member changed the map")
        return values
    class_entry, node_entry = actual.EntriesValue[len(before):]
    require(node.ClassValue == ROLES[owner["field"]] and node.StartOffset == 0 and node.EndOffset == len(data)
            and node.IndexValue == node_entry.IndexValue == owner["object_slot"]
            and node_entry.EntryValue is node
            and class_entry.IndexValue == owner["new_class_slot"]
            and class_entry.EntryValue == node.ClassValue, "native root, class slot or extent changed")
    fields = node.FieldsValue
    values.update(class_slot=class_entry.IndexValue, class_name=node.ClassValue.NameValue,
                  feature_index=fields["f08"], resolved_items=len(fields["f60"]["list"]["items"]),
                  xml_layout="moFeature_c.SerializeXmlData" in graph.ReportValue["used_schemas"])
    if node.ClassValue == KSketchBlockClass:
        fixed = graph.ReportValue["native_byte_fields"]
        guid = fields["f380"]
        require(len(guid) == 16 and digest(guid) == owner["guid_sha256"] and len(fixed) == 1
                and fields["blocks"]["f30"] is node and fields["blocks"]["n70"] == fields["blocks"]["n98"] == 0,
                "the sketch guid or map backlink changed")
        values.update(guid_sha256=digest(guid), backlink_slot=fields["blocks"]["f30"].IndexValue,
                      fixed_fields=list(fixed))
    else:
        require(not graph.ReportValue["native_byte_fields"] and fields["f368"] == {"n": 0, "items": []},
                "the empty exploded word map changed")
        values.update(word_map_count=fields["f368"]["n"])
    return values


def unsupported_virtual(data, seed, role):
    virtuals = dict(KMemberVirtuals)
    del virtuals[(role.NameValue, 1208)]
    context = BodyContext(19000, KMemberLayouts, virtuals, KCfgMemberSchemas)
    reader = GraphReader(BinaryReader(data), ArchiveMaps(seed.CounterValue, seed),
                         partial(ReadBodyMut, context))
    try:
        ReadNodeMut(reader)
    except ValueError as error:
        require("unsupported SOLIDWORKS body virtual slot 0x4b8" in str(error),
                "missing virtual failed at the wrong boundary")
        return "missing_virtual"
    raise ValueError("a missing virtual selected a fallback")


def ladder_refusals(group):
    owner, data, graph, seed = group[0]
    start = owner["interval"][0]
    guid_end = owner["guid_interval"][1] - start
    link = owner["map_backlink"] - start
    length = owner["map_length"] - start
    name_flag = owner["optional_name_flag"] - start
    role = KSketchBlockClass
    color = next(entry.IndexValue for entry in seed.EntriesValue
                 if getattr(entry.EntryValue, "ClassValue", None) == KFeatColorClass)
    offset_seed = MapSnapshot(seed.CounterValue + 3, seed.EntriesValue)
    return [
        refuse("truncated_guid", data[:guid_end - 1], seed, role, "truncated SOLIDWORKS archive field"),
        refuse("trailing", data + b"\0", seed, role, "trailing data"),
        refuse("wrong_owner", data, seed, KExplViewClass, "unsupported body owner"),
        refuse("wrong_archive_version", data, seed, role, "archive version 19000", 18900),
        refuse("wrong_map_counter", data, offset_seed, role, "unresolved external object"),
        refuse("null_backlink", data[:link] + b"\0\0" + data[link + 2:], seed, role, "owning backlink"),
        refuse("inherited_backlink", data[:link] + pack("<H", color) + data[link + 2:], seed, role, "owning backlink"),
        refuse("reused_root", pack("<H", graph.RootValue.IndexValue), graph.MapValue, role, "new root object"),
        refuse("populated_name", data[:name_flag] + b"\x01\x01X" + data[name_flag + 1:], seed, role, "populated SOLIDWORKS feature owner"),
        refuse("populated_map", data[:length] + pack("<iii", 1, 23, 0) + data[length + 4:], seed, role, "populated SOLIDWORKS sketch block maps"),
        unsupported_virtual(data, seed, role),
    ]


def native_case(name):
    config, case, previous = load_case(name)
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    groups, rows = [], []
    for owner in case["owners"]:
        start, end = owner["interval"]
        data = config[start:end]
        require(digest(data) == owner["sha256"], "wrong bounded native member")
        seed = MapSnapshot(owner["counter"][0], previous.EntriesValue)
        graph = ReadCfgMember(data, 19000, seed, ROLES[owner["field"]])
        rows.append(inspect(graph, owner, data, seed))
        groups.append((owner, data, graph, seed))
        previous = graph.MapValue
    return {"records": rows, "runtime_external_accesses": 0,
            "refusals": ladder_refusals(groups) if name == "ladder" else []}


def main():
    parser = ArgumentParser(description="Verify the bounded ordinary Config-0 feature owner records")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(native_case(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
