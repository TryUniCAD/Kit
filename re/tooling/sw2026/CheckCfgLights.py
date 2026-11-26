from argparse import ArgumentParser
from codecs import lookup
import json
from pathlib import Path
from struct import pack, unpack_from
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, refuse, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Config.Members.ReadCfgMember import ReadCfgMember
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import (
    KAmbientClass, KDirectionClass, KEnvFolderClass, KNodeNameClass,
)
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNodeTagMut import ReadNodeTagMut
from convert.adapters.solidworks.Archive.Reading.ReadTypeDescMut import ReadTypeDescMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigSceneSource01.json"
COUNTS_MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigSceneCounts01.json"
NATIVE_COUNTS = ("one", "two")


def input_config(case):
    source = COUNTS_MANIFEST if case in NATIVE_COUNTS else MANIFEST
    manifest = json.loads(source.read_bytes())
    entry = manifest["controls"][case]
    raw = (ROOT / entry["path"]).read_bytes()
    require(digest(raw) == entry["part_sha256"], "native source changed")
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == manifest["archive_version"] == 19000,
            "wrong native archive version")
    config = archive.require(manifest["stream"])
    require(digest(config) == entry["config_sha256"], "physical configuration changed")
    if case in NATIVE_COUNTS:
        require(len(raw) == entry["part_bytes"] and len(config) == entry["config_bytes"],
                "native count source sizes changed")
        for stream, expected in entry["linked_streams"].items():
            data = archive.require(stream)
            require(len(data) == expected["bytes"] and digest(data) == expected["sha256"],
                    f"native count linked stream changed: {stream}")
    return config, entry


def record_bytes(config, record):
    first, last = record["bounds"]
    data = config[first:last]
    require(digest(data) == record["sha256"], "native scene record or interval changed")
    return data


def read_count_root(config, case):
    original = case["part_root"]
    data = record_bytes(config, original)
    cursor = BinaryReader(data)
    tag = ReadNodeTagMut(cursor, 0, 128)
    descriptor = ReadTypeDescMut(cursor)
    require(tag.KindValue == "NewClass" and cursor.GetRemaining() == 0
            and descriptor == RuntimeClass("moPart_c", 1)
            and original["complete_end"] == len(config),
            "native count control model root changed")
    return digest(data)


def scene_seed(config, case):
    name = case["earlier_name"]
    data = record_bytes(config, name)
    start, end = name["counter"]
    graph = ReadCfgMember(data, 19000, MapSnapshot(start, ()), KNodeNameClass)
    class_entry, object_entry = graph.MapValue.EntriesValue
    node = graph.RootValue
    require(class_entry.EntryValue is node.ClassValue and node.ClassValue == KNodeNameClass
            and object_entry.EntryValue is node and node.IndexValue == name["object_slot"]
            and class_entry.IndexValue == name["class_slot"]
            and node.StartOffset == 0 and node.EndOffset == len(data)
            and graph.MapValue.CounterValue == end, "actual earlier name map entries differ")
    if "name" in name:
        require(node.FieldsValue["f08"] == name["name"], "native part name changed")
    return MapSnapshot(case["scene_counter"][0], graph.MapValue.EntriesValue)


def children(root):
    fields = root.FieldsValue["f60"]
    return [row["o"] for row in fields["list"]["items"]]


def read_scene(config, case, data, seed):
    graph = ReadCfgMember(data, 19000, seed, KEnvFolderClass)
    members = graph.MapValue.EntriesValue
    before = seed.EntriesValue
    require(graph.ReportValue["completed"] and graph.MapValue.CounterValue == case["scene_counter"][1]
            and all(a is b for a, b in zip(members[:len(before)], before, strict=True)),
            "inherited scene membership or final counter changed")
    values = {entry.IndexValue: entry.EntryValue for entry in members}
    root = graph.RootValue
    start = case["scene"][0]["bounds"][0]
    rows = []
    owned_lights = children(root)
    if "directional_count" in case:
        first, final = case["list_count_span"]
        require(final - first == 2 and final == case["scene"][1]["bounds"][0],
                "native count word or first light boundary changed")
        stored, = unpack_from("<H", config, first)
        require(stored == len(owned_lights) == case["directional_count"] + 1,
                "native and decoded light counts differ")
    for node, expected in zip((root, *owned_lights), case["scene"], strict=True):
        row = scene_row(config, start, node, expected, values)
        rows.append(row)
    return rows, graph.ReportValue["field_calls"].get("Normalize", 0)


def scene_row(config, start, node, expected, entries):
    bounds = expected["bounds"]
    fields = node.FieldsValue
    name = fields["f18"]
    record_bytes(config, expected)
    require(node.ClassValue.NameValue == expected["class"] and node.ClassValue.SchemaValue == 1
            and [node.StartOffset + start, node.EndOffset + start] == bounds
            and [name.StartOffset + start, name.EndOffset + start] == expected["name_bounds"]
            and entries[expected["class_slot"]] is node.ClassValue
            and entries[expected["object_slot"]] is node and node.IndexValue == expected["object_slot"]
            and entries[expected["name_slot"]] is name and name.IndexValue == expected["name_slot"]
            and entries[4] is name.ClassValue, "scene class reuse or object ownership differs")
    result = {"class": expected["class"], "slots": [expected[key] for key in ("class_slot", "object_slot", "name_slot")],
              "name": name.FieldsValue["f08"], "record_bytes": bounds[1] - bounds[0]}
    if "name_sha256" in expected:
        first, final = expected["name_bounds"]
        require(digest(config[first:final]) == expected["name_sha256"]
                and result["name"] == expected["name"]
                and fields["f08"] == expected["native_f08"],
                "native count control name or feature word changed")
        result["native_f08"] = fields["f08"]
    if "normalized_word_offset" in expected:
        raw, = unpack_from("<i", config, expected["normalized_word_offset"])
        require(fields["f36c#wire"] == raw and fields["f36c"] == 0
                and fields["f500"] == {"n": 0, "props": []}, "normalization or empty property scope differs")
        if "name_sha256" in expected:
            count, = unpack_from("<i", config, expected["property_count_offset"])
            require(count == 0, "native light property count changed")
        result.update(normalization=[raw, fields["f36c"]], state=[fields["state#wire"], fields["state"]])
    if node.ClassValue == KDirectionClass:
        result["direction"] = [fields["f3b0"][axis] for axis in ("x", "y", "z")]
        if "direction" in expected:
            require(result["direction"] == expected["direction"], "native directional vector changed")
    return result


def replace_at(data, start, end, value):
    return data[:start] + value + data[end:]


def contrast_words(data, case, seed):
    root, ambient = case["scene"]
    start = root["bounds"][0]
    variant = data
    for key, word in (("normalized_word_offset", -739), ("first_shadow_offset", 27), ("second_shadow_offset", -16)):
        offset = ambient[key] - start
        variant = replace_at(variant, offset, offset + 4, pack("<i", word))
    graph = ReadCfgMember(variant, 19000, seed, KEnvFolderClass)
    light, = children(graph.RootValue)
    fields = light.FieldsValue
    return [fields[key] for key in ("f36c#wire", "f36c", "f384#0", "f384")]


def small_refusals(case, data, seed):
    root, ambient = case["scene"]
    start = root["bounds"][0]
    floor, ceil = (value - start for value in root["name_bounds"])
    first, last = (value - start for value in case["list_count_span"])
    ambient_start, ambient_end = (position - start for position in ambient["bounds"])
    property_offset = ambient["property_count_offset"] - start
    normal_offset = ambient["normalized_word_offset"] - start
    wrong_name = b"moPMarkRecord_c"
    wrong_tag = pack("<HHH", 0xffff, 1, len(wrong_name)) + wrong_name
    role = KEnvFolderClass
    return [
        refuse("truncated_word", data[:normal_offset + 3], seed, role, "truncated SOLIDWORKS archive field"),
        refuse("trailing", data + b"\0", seed, role, "trailing data"),
        refuse("wrong_version", data, seed, role, "archive version 19000", 18900),
        refuse("null_scene", b"\0\0", seed, role, "environment folder member requires its concrete root"),
        refuse("light_as_root", data[ambient_start:ambient_end], seed, KAmbientClass, "unsupported role"),
        refuse("unknown_nested_role", replace_at(data, floor, ceil, wrong_tag), seed, role, "unsupported body owner"),
        refuse("borrowed_name", replace_at(data, floor, ceil, pack("<H", case["earlier_name"]["object_slot"])),
               seed, role, "cannot borrow an earlier object"),
        refuse("populated_property", replace_at(data, property_offset, property_offset + 4, pack("<i", 1)),
               seed, role, "populated light user properties"),
        refuse("empty_scene", replace_at(data, first, ambient_end, b"\0" * (last - first)),
               seed, role, "unsupported SOLIDWORKS scene light ownership"),
        refuse("missing_inherited_name", data, MapSnapshot(seed.CounterValue, ()), role, "archive class reference"),
    ]


def counted_variants(case, data, seed):
    root, ambient, *directions = case["scene"]
    start = root["bounds"][0]
    floor, ceil = (offset - start for offset in case["list_count_span"])
    row_end = directions[-1]["bounds"][1] - start
    require(ceil - floor == 2 and ceil == ambient["bounds"][0] - start,
            "the counted light row boundary changed")
    variants = []
    for count in (1, 2):
        end = directions[count - 1]["bounds"][1] - start
        variant = data[:floor] + pack("<H", 1 + count) + data[ceil:end] + data[row_end:]
        graph = ReadCfgMember(variant, 19000, seed, KEnvFolderClass)
        node = graph.RootValue
        values = children(node)
        require(graph.ReportValue["completed"] and node.StartOffset == 0 and node.EndOffset == len(variant)
                and [light.ClassValue for light in values] == [KAmbientClass, *([KDirectionClass] * count)]
                and all(a is b for a, b in zip(graph.MapValue.EntriesValue[:len(seed.EntriesValue)],
                                             seed.EntriesValue, strict=True)),
                "counted lights changed order, framing or inherited map identities")
        variants.append({"directional_count": count,
                         "slots": [light.IndexValue for light in values],
                         "counter": [seed.CounterValue, graph.MapValue.CounterValue]})
    return variants


def repeated_light(case, data, seed):
    start = case["scene"][0]["bounds"][0]
    earlier, next_light = case["scene"][2:4]
    first, last = (offset - start for offset in next_light["bounds"])
    return refuse("repeated_light", replace_at(data, first, last, pack("<H", earlier["object_slot"])),
                  seed, KEnvFolderClass, "unsupported SOLIDWORKS scene light ownership")


def run(name):
    config, case = input_config(name)
    for text_encoding in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(text_encoding)
    sys.addaudithook(audit_run)
    seed = scene_seed(config, case)
    data = record_bytes(config, case["scene"][0])
    rows, normalized = read_scene(config, case, data, seed)
    report = {"owner": case["parent_member"], "counter": case["scene_counter"], "members": rows,
              "inherited_slots": [entry.IndexValue for entry in seed.EntriesValue],
              "normalization_calls": normalized, "runtime_external_accesses": 0}
    if name == "concave":
        report.update(contrasted_words=contrast_words(data, case, seed), refusals=small_refusals(case, data, seed))
    elif name == "ladder":
        report["counted_variants"] = counted_variants(case, data, seed)
        report["refusals"] = [repeated_light(case, data, seed)]
    else:
        report.update(part_root_sha256=read_count_root(config, case),
                      scene_span=case["scene"][0]["bounds"], scene_sha256=digest(data),
                      directional_count=len(rows) - 2)
    return report


def main():
    parser = ArgumentParser(description="Verify the bounded ordinary Config-0 scene owner")
    parser.add_argument("case", choices=("ladder", "concave", *NATIVE_COUNTS))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
