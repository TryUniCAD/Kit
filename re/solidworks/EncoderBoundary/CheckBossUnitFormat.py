from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
from struct import unpack_from
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ComposeExactSketchPresentation import (
    SldprtArchive, canonical_json, demand, digest, generate, read_record, write_artifact,
)
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


def project(value):
    if isinstance(value, ArchiveNode):
        return {"class": value.ClassValue.NameValue, "fields": project(value.FieldsValue)}
    if isinstance(value, dict):
        return {key: project(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [project(item) for item in value]
    if type(value) is float:
        return value.hex()
    demand(value is None or type(value) in (str, bool, int), "unsupported unit field")
    return value


def unit_tables(archive):
    fields = ReadPartConfig(archive).RootValue.FieldsValue
    return {
        owner: None if fields[owner] is None else {
            row["o"].ClassValue.NameValue: row["o"] for row in fields[owner].FieldsValue["items"]
        }
        for owner in ("f9b8", "f9c0")
    }


def precision_offsets(config, table, precision):
    offsets = []
    for row in table.values():
        start = row.StartOffset
        tag, = unpack_from("<H", config, start)
        if tag == 0xFFFF:
            width, = unpack_from("<H", config, start + 4)
            offset = start + 6 + width
        else:
            demand(tag & 0x8000, "unit precision must belong to a concrete object")
            offset = start + 2
        demand(unpack_from("<i", config, offset) == (precision,)
               and row.FieldsValue["f0c"] == precision and offset + 4 <= row.EndOffset,
               "stored f0c differs from its typed unit field")
        offsets.append(offset)
    return sorted(offsets)


def read_case(directory):
    evidence = read_record((directory / "Evidence.json").read_bytes())
    name = PureWindowsPath(evidence["native_locator"]).name
    custody = evidence["archive"]
    raw = (directory / name).read_bytes()
    demand(custody == {"path": name, "bytes": len(raw), "sha256": digest(raw)}
           and evidence["external_generation_attempts"] == evidence["native_launches"] == 0,
           "candidate custody or construction audit differs")
    archive = SldprtArchive.from_bytes(raw, "<generated unit-format contrast>")
    return evidence, archive


def compare(args):
    directories = (args.control, args.explicit_four, args.precision, args.repeat)
    demand(len({path.resolve() for path in directories}) == len(directories), "expected four distinct replay outputs")
    control, high = read_case(args.control)
    explicit_four, _ = read_case(args.explicit_four)
    precision, low = read_case(args.precision)
    repeat, _ = read_case(args.repeat)
    demand(control["archive"]["sha256"] == args.control_sha and control == explicit_four and precision == repeat,
           "default generation changed or precision 2 did not replay")
    demand(control | {"archive": precision["archive"]} == precision, "unrelated typed readback changed")
    demand(set(high.streams) == set(low.streams), "clear stream roster changed")
    section = "Contents/Config-0"
    clear_high, clear_low = high.Require(section), low.Require(section)
    demand(all(high.Require(name) == low.Require(name) for name in high.streams if name != section)
           and len(clear_high) == len(clear_low), "unrelated clear bytes or Config-0 width changed")

    high_tables, low_tables = unit_tables(high), unit_tables(low)
    high_doc, low_doc = high_tables["f9b8"], low_tables["f9b8"]
    offsets = precision_offsets(clear_high, high_doc, 4)
    demand(offsets == precision_offsets(clear_low, low_doc, 2)
           and len(offsets) == 16
           and offsets == [index for index, (prior, after) in enumerate(zip(clear_high, clear_low, strict=True))
                           if prior != after],
           "changed Config-0 bytes are not entirely the sixteen f0c precision words")
    demand(project(high_tables["f9c0"]) == project(low_tables["f9c0"]),
           "separately owned analysis table changed")

    native = args.stock.read_bytes()
    demand(digest(native) == args.stock_sha, "native stock digest differs")
    stock = unit_tables(SldprtArchive.from_bytes(native, "<native stock comparison only>"))
    native_rows = stock["f9b8"]
    demand(native_rows.keys() == low_doc.keys() and stock["f9c0"] is None,
           "native stock unit ownership differs")
    remaining = {}
    for kind, native_row in native_rows.items():
        native_fields = project(native_row.FieldsValue)
        generated_fields = project(low_doc[kind].FieldsValue)
        changes = {key: [native_fields.get(key), generated_fields.get(key)]
                   for key in native_fields.keys() | generated_fields.keys()
                   if native_fields.get(key) != generated_fields.get(key)}
        if changes:
            remaining[kind] = changes
    result = {
        "schema": "kit.research.boss-unit-format.v1",
        "request_sha256": precision["request_sha256"],
        "default_archive": control["archive"],
        "explicit_four_archive": explicit_four["archive"],
        "precision_archive": precision["archive"],
        "repeat_archive": repeat["archive"],
        "native_locator": precision["native_locator"],
        "written_at": precision["written_at"],
        "changed_stream": {"name": section, "bytes": len(clear_high), "default_sha256": digest(clear_high),
                           "precision_sha256": digest(clear_low), "changed_byte_offsets": offsets},
        "equal_clear_streams": len(high.streams) - 1,
        "stock_sha256": args.stock_sha,
        "stock_precision_by_class": {kind: row.FieldsValue["f0c"] for kind, row in native_rows.items()},
        "stock_associated_analysis_table": False,
        "generated_analysis_rows": len(low_tables["f9c0"]),
        "stock_to_generated_2_remaining_unit_fields": remaining,
        "fields": precision["fields"],
        "strict_readback": precision["strict_readback"],
        "external_generation_attempts": precision["external_generation_attempts"],
        "native_launches": precision["native_launches"],
    }
    write_artifact(args.output.parent, args.output.name, canonical_json(result))
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Research SOLIDWORKS boss document unit precision")
    commands = parser.add_subparsers(dest="command", required=True)
    writer = commands.add_parser("generate")
    writer.add_argument("--request", type=Path, required=True)
    writer.add_argument("--output", type=Path, required=True)
    writer.add_argument("--locator", required=True)
    writer.add_argument("--epoch", type=int, required=True)
    writer.add_argument("--precision", type=int, required=True, choices=(2, 4))
    reader = commands.add_parser("compare")
    for option in ("control", "explicit-four", "precision", "repeat", "stock", "output"):
        reader.add_argument("--" + option, type=Path, required=True)
    reader.add_argument("--stock-sha", required=True)
    reader.add_argument("--control-sha", required=True)
    args = parser.parse_args()
    result = generate(args, document_decimal_places=args.precision) if args.command == "generate" else compare(args)
    sys.stdout.buffer.write(canonical_json(result))
