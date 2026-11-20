from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag


def encode_row(row, *, source_frame):
    tag, label, integer, single, double = row
    return b"".join(
        (
            EncodeTag(ArchiveTag(*tag)),
            EncodeString(CStringValue(*label), IsSourceFrame=source_frame),
            EncodeScalar(integer, "i32"),
            EncodeScalar(single, "f32"),
            EncodeScalar(double, "f64"),
        )
    )


def encode_group(group, *, source_frame):
    rows = group["rows"]
    return b"".join(
        (
            EncodeTag(ArchiveTag(*group["tag"])),
            EncodeString(CStringValue(*group["label"]), IsSourceFrame=source_frame),
            EncodeCount(group["vendor_count"]),
            EncodeCount(group["framework_count"], IsFramework=True),
            EncodeCount(len(rows)),
            b"".join(encode_row(row, source_frame=source_frame) for row in rows),
        )
    )


def encode_record(groups, *, source_frame):
    return b"".join(
        (
            EncodeScalar(4, "i32"),
            EncodeScalar(1, "i32"),
            EncodeCount(len(groups)),
            b"".join(encode_group(group, source_frame=source_frame) for group in groups),
        )
    )


def read_tag(cursor):
    tag, cursor.OffsetValue = ReadTag(cursor.BytesValue, cursor.OffsetValue)
    return [tag.KindValue, tag.IndexValue]


def read_label(cursor):
    label = ReadCStringMut(cursor)
    return [label.TextValue, label.IsUnicode]


def read_count(cursor, *, framework):
    count, cursor.OffsetValue = ReadCount(
        cursor.BytesValue, cursor.OffsetValue, IsFramework=framework
    )
    return count


def read_bounded_count(cursor, min_size):
    try:
        return ReadCountMut(cursor, min_size)
    except ValueError as error:
        raise ValueError(f"{error} at byte {cursor.GetOffset()}") from None


def read_row(cursor):
    return [
        read_tag(cursor),
        read_label(cursor),
        ReadScalarMut(cursor, "i32"),
        ReadScalarMut(cursor, "f32"),
        ReadScalarMut(cursor, "f64"),
    ]


def read_group(cursor):
    return {
        "tag": read_tag(cursor),
        "label": read_label(cursor),
        "vendor_count": read_count(cursor, framework=False),
        "framework_count": read_count(cursor, framework=True),
        "rows": [read_row(cursor) for _ in range(read_bounded_count(cursor, 19))],
    }


def read_record(data):
    version_at, _ = ReadScalar(data, 0, "i32")
    version, groups_at = ReadScalar(data, version_at, "i32")
    if version != 1:
        raise ValueError("unexpected synthetic archive wire version")
    cursor = BinaryReader(data, groups_at)
    groups = [read_group(cursor) for _ in range(read_bounded_count(cursor, 9))]
    if cursor.GetRemaining():
        raise ValueError("synthetic archive record retains unread bytes")
    return groups


def main():
    parser = ArgumentParser(description="Compare synthetic archive wire records")
    parser.add_argument("mode", choices=("write", "read", "replay"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    if options.mode == "read":
        payload = dumps(read_record(options.source.read_bytes())).encode("utf-8")
    else:
        groups = loads(options.source.read_text(encoding="utf-8"))
        payload = encode_record(groups, source_frame=options.mode == "replay")
    with options.output.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
