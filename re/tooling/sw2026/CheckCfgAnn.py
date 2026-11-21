from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from TraceCfgFont import audit_run, descriptor
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Config.Annotations.AnnLayouts import KAnnDefs, KAnnLayouts, KTolHelper
from convert.adapters.solidworks.Archive.Config.Annotations.ReadCfgAnn import ReadCfgAnn
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigAnnotationSource01.json"
BASE = "moBaseAnnotationDefs_c"
FRAME = "moGTolDlgDataFrame_c"
LAYERS = 0x40000000


def digest(data):
    return sha256(data).hexdigest()


def save_fields(fields, layout, part, conditions):
    maps = ArchiveMaps(part.BaseValue, part.MapValue)
    writer = BodyWriter(maps, BodyContext(19000, KAnnLayouts, {}, {}, FlagsValue={"conditions": conditions}), WriteBodyMut)
    WriteSchemaMut(WriteFrame(writer, FieldScope(fields), part.RootValue, WriteSchemaMut, WriteFieldsMut), layout)
    assert maps.Snapshot() == part.MapValue and not writer.NestingDepth and not part.RootValue.FieldsValue
    assert not writer.ContextValue.UsageValue.SchemaPath and not writer.ContextValue.UsageValue.FieldPath
    return bytes(writer.OutputValue)


def source_case(config, part, case):
    aliases = HeaderRefNodes(part.HeaderValue, 19000)
    root_class, root_entry, alias = part.MapValue.EntriesValue
    assert part.BaseValue == part.MapValue.CounterValue == 4 and len(aliases) == 1
    assert root_class.EntryValue is part.RootValue.ClassValue and root_entry.EntryValue is part.RootValue
    assert alias.EntryValue is aliases[0]
    fields, ranges = {}, {}
    for layout, site in ((KAnnDefs, "f1f18"), (KTolHelper, "f9a0")):
        row, = [item for item in case["rows"] if item["layout"] == layout]
        assert row["field_path"][-2:] == ["fae0", site] and row["conditions"] == 0
        assert [root_class.IndexValue, root_entry.IndexValue, alias.IndexValue] == row["map_anchor_slots"]
        assert descriptor(part.RootValue) == row["part"] and descriptor(alias.EntryValue) == row["alias"]
        data = config[slice(*row["interval"])]
        assert digest(data) == row["wire_sha256"]
        model = ReadCfgAnn(data, 19000, part, layout)
        assert save_fields(model, layout, part, row["conditions"]) == data
        fields[layout], ranges[layout] = model, row["interval"]
    base_members = ("f2c0", "f418", "f250", "f1e8", "f108", "fa0", "f178", "f4a0", "f40", "f398")
    base_rows = {row["field_path"][5]: row for row in case["rows"] if row["layout"] == BASE}
    defaults = fields[KAnnDefs]
    assert len(base_rows) == len(base_members)
    for name in base_members:
        native = base_rows[name]
        raw = config[slice(*native["interval"])]
        assert native["selectors"] == {"f44": -1} and defaults[name]["f44"] == -1 and "f48" not in defaults[name]
        assert digest(raw) == native["wire_sha256"] and save_fields(defaults[name], BASE, part, 0) == raw
    frames = [row for row in case["rows"] if row["layout"] == FRAME]
    model = fields[KTolHelper]
    assert model["n08"] == len(frames) == len(model["f08"]) == 2
    for row, item in zip(frames, model["f08"], strict=True):
        assert row["field_path"][-4:] == ["fae0", "f9a0", "f08", "e"]
        assert row["selectors"] == {"f10": None, "f18": None, "f148": 0, "n2b8": 0}
        frame_data = config[slice(*row["interval"])]
        assert digest(frame_data) == row["wire_sha256"] and save_fields(item["e"], FRAME, part, 0) == frame_data
    return {"scopes": ranges, "member_lengths": [len(config[slice(*ranges[key])]) for key in (KAnnDefs, KTolHelper)],
            "source_sha256": case["part_sha256"], "body_sha256": [digest(config[slice(*ranges[key])]) for key in (KAnnDefs, KTolHelper)],
            "map_inherited": [entry.IndexValue for entry in part.MapValue.EntriesValue],
            "native_incoming_counter": base_rows["f2c0"]["map_counter"], "frame_spans": [row["interval"] for row in frames],
            "annotation_base_count": len(base_members), "unchanged_archive_bodies": len(fields) + len(base_rows) + len(frames)}


def ansi(text):
    return bytes((len(text),)) + text.encode("ascii")


def wide(text):
    return b"\xff\xfe\xff" + bytes((len(text),)) + text.encode("utf-16-le")


def independent_frame(*, first=b"\0\0", second=b"\0\0", datum=0, indicators=0):
    strings = pack("<H", 2) + ansi("tolerance") + wide("Ω")
    empty = pack("<H", 0)
    return b"".join((ansi("shape"), b"\x81", wide("δ"), ansi("value"), b"\xe2", ansi("A"), wide("Ø"),
                     strings, empty, empty, empty, empty, empty, pack("<iiH", -17, 0x76543210, datum),
                     first, second, pack("<i", indicators)))


def wire_cases(config, part, case):
    frames = [row for row in case["rows"] if row["layout"] == FRAME]
    helper, = [row for row in case["rows"] if row["layout"] == KTolHelper]
    annotation, = [row for row in case["rows"] if row["layout"] == KAnnDefs]
    suffix = config[frames[-1]["interval"][1]:helper["interval"][1]]
    defs = config[slice(*annotation["interval"])]
    defaults = ReadCfgAnn(defs, 19000, part, KAnnDefs)
    assert ReadCfgAnn(defs, 19000, part, KAnnDefs, Conditions=LAYERS) == defaults
    assert save_fields(defaults, KAnnDefs, part, LAYERS) == defs
    selector = 52 + 36
    assert defs[selector:selector + 2] == pack("<h", -1)
    marked = defs[:selector] + pack("<h", -2) + defs[selector + 2:]
    marked_fields = ReadCfgAnn(marked, 19000, part, KAnnDefs)
    assert marked_fields["f2c0"]["f44"] == -2 and save_fields(marked_fields, KAnnDefs, part, 0) == marked
    independent = pack("<i", 1) + independent_frame() + suffix
    emitted = ReadCfgAnn(independent, 19000, part, KTolHelper)
    frame, = [row["e"] for row in emitted["f08"]]
    assert emitted["n08"] == 1 and frame["f58"]["n"] == 2
    assert frame["f58"]["items"] == [{"s": ("A", "tolerance")}, {"s": "Ω"}]
    assert (frame["f08"], frame["f28"], frame["f30"], frame["f40"], frame["f20"], frame["f24"]) == (
        ("A", "shape"), 0x81, "δ", 0xe2, -17, 0x76543210,
    )
    assert save_fields(emitted, KTolHelper, part, 0) == independent
    empty = pack("<i", 0) + suffix
    absent = ReadCfgAnn(empty, 19000, part, KTolHelper)
    assert absent["f08"] == [] and save_fields(absent, KTolHelper, part, 0) == empty
    foreign = b"moAnnotationView_c"
    tag = pack("<HHH", 0xffff, 1, len(foreign)) + foreign
    refusals = []

    def refuse(label, wire, root, expected, *, version=19000, conditions=0, prefix=part):
        before = tuple(prefix.MapValue.EntriesValue)
        try:
            ReadCfgAnn(wire, version, prefix, root, Conditions=conditions)
        except ValueError as error:
            assert expected in str(error), (label, str(error))
        else:
            raise ValueError(f"unexpected archive admission: {label}")
        assert tuple(prefix.MapValue.EntriesValue) == before and not part.RootValue.FieldsValue
        refusals.append(label)

    refuse("truncated", independent[:-1], KTolHelper, "truncated SOLIDWORKS archive field")
    refuse("trailing", independent + b"\0", KTolHelper, "bounded body or map")
    refuse("older_archive", independent, KTolHelper, "requires archive version 19000", version=18900)
    refuse("foreign_inline", independent, "moAnnotationView_c", "unsupported inline owner")
    refuse("foreign_part", independent, KTolHelper, "requires its enclosing part", prefix=replace(part, RootValue=part.HeaderValue))
    refuse("layer_reference", marked, KAnnDefs, "moBaseAnnotationDefs_c.f48 layer object", conditions=LAYERS)
    refuse("part_reference", pack("<i", 1) + independent_frame(first=pack("<H", 2)) + suffix, KTolHelper, "unqualified reference owner")
    refuse("header_reference", pack("<i", 1) + independent_frame(second=pack("<H", 3)) + suffix, KTolHelper, "unqualified reference owner")
    refuse("new_class", pack("<i", 1) + independent_frame(first=tag) + suffix, KTolHelper, "unsupported SOLIDWORKS body class moAnnotationView_c schema 1")
    refuse("datum_owners", pack("<i", 1) + independent_frame(datum=1) + suffix, KTolHelper, "moGTolDlgDataFrame_c datum owners")
    refuse("indicator_owners", pack("<i", 1) + independent_frame(indicators=1) + suffix, KTolHelper, "moGTolDlgDataFrame_c indicator owners")
    refuse("negative_indicator_count", pack("<i", 1) + independent_frame(indicators=-1) + suffix, KTolHelper, "unqualified indicator count")
    refuse("negative_frame_count", pack("<i", -1) + suffix, KTolHelper, "nonnegative frame count")
    return {"refusals": refusals, "positive_archives": 4, "different_frame_rows": [emitted["n08"], absent["n08"]],
            "string_array_count": frame["f58"]["n"], "signed_layer_selector": marked_fields["f2c0"]["f44"],
            "source_sha256": case["part_sha256"]}


def main():
    cli = ArgumentParser()
    cli.add_argument("case", choices=("ladder", "concave", "wire"))
    selected = cli.parse_args().case
    trace = json.loads(MANIFEST.read_bytes())
    case = trace["cases"]["ladder" if selected == "wire" else selected]
    source = (ROOT / case["path"]).read_bytes()
    assert digest(source) == case["part_sha256"] and trace["archive_version"] == 19000
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)
    archive = SldprtArchive.from_bytes(source)
    config, header = (archive.Require(key) for key in ("Contents/Config-0", "Contents/Config-0-ModelHeader"))
    assert digest(config) == case["config_sha256"] and digest(header) == case["header_sha256"] and len(config) == case["config_bytes"]
    part = ReadPartStart(archive)
    result = wire_cases(config, part, case) if selected == "wire" else source_case(config, part, case)
    print(json.dumps(result | {"case": selected, "runtime_external_accesses": 0, "native_launches": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
