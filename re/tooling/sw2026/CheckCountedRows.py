from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from functools import partial
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
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadArrayMut import ReadArrayMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import WriteArrayMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


ROW_FIELDS = (NativeField("Scalar", "value", "i32"),)
ARRAY_FIELDS = (
    NativeField("Array", "rows", "Count", BodyValue=ROW_FIELDS, CountValue="row_count"),
    NativeField(
        "Array",
        "framework_rows",
        "Framework",
        BodyValue=ROW_FIELDS,
    ),
    NativeField(
        "Array",
        "signed_rows",
        "i32",
        BodyValue=ROW_FIELDS,
        CountValue="signed_count",
        ModeValue="Positive",
    ),
    NativeField(
        "Array",
        "split_rows",
        "Split",
        BodyValue=ROW_FIELDS,
        CountValue="split_high",
        OtherName="split_low",
        ModeValue="Unsigned",
    ),
    NativeField(
        "Array", "combined_rows", "Split", BodyValue=ROW_FIELDS, ModeValue="Combined"
    ),
)


def reject_nested(*args):
    raise ValueError("the synthetic counted record contains only scalar rows")


def read_fields(observed, frame, fields):
    observed.append(frame.ScopeValue)
    for field in fields:
        frame.ScopeValue.FieldsValue[field.NameValue] = ReadScalarMut(
            frame.ReaderValue.Cursor, field.TypeValue
        )


def write_fields(observed, frame, fields):
    observed.append(frame.ScopeValue)
    for field in fields:
        value = ReadScopeValue(frame.ScopeValue, field.NameValue)
        frame.WriterValue.OutputValue.extend(EncodeScalar(value, field.TypeValue))


def verify_rows(scope, name, observed):
    rows = scope.FieldsValue[name]
    for index, (child, row) in enumerate(zip(observed, rows, strict=True)):
        if (
            child.IndexValue != index
            or child.ParentValue is not scope
            or child.FieldsValue is not row
        ):
            raise ValueError("counted rows lost their index, parent or field mapping")
    observed.clear()


def read_record(payload, rules):
    context = BodyContext(19000, {}, {}, {})
    cursor = BinaryReader(payload)
    reader = GraphReader(cursor, ArchiveMaps(1), reject_nested)
    fields = {}
    node = ArchiveNode(RuntimeClass("RowProbe", 1), fields)
    scope = FieldScope(fields)
    observed = []
    frame = ReadFrame(
        context, reader, scope, node, reject_nested, partial(read_fields, observed)
    )
    for rule in rules:
        start = cursor.OffsetValue
        previous_fields = deepcopy(fields)
        previous_values = deepcopy(scope.ValuesValue)
        try:
            ReadArrayMut(frame, rule)
        except ValueError as error:
            intact = (
                cursor.OffsetValue == start
                and fields == previous_fields
                and scope.ValuesValue == previous_values
            )
            raise ValueError(
                f"{error}; array checkpoint {start}, cursor {cursor.OffsetValue}, "
                f"scope intact {intact}"
            ) from None
        verify_rows(scope, rule.NameValue, observed)
    if cursor.GetRemaining():
        raise ValueError("synthetic counted record retains unread bytes")
    return fields


def write_record(fields, rules, expected_widths):
    before = deepcopy(fields)
    context = BodyContext(19000, {}, {}, {})
    writer = BodyWriter(ArchiveMaps(1), context, reject_nested)
    node = ArchiveNode(RuntimeClass("RowProbe", 1), fields)
    scope = FieldScope(fields)
    observed = []
    frame = WriteFrame(writer, scope, node, reject_nested, partial(write_fields, observed))
    for rule in rules:
        WriteArrayMut(frame, rule)
        verify_rows(scope, rule.NameValue, observed)
    if fields != before or ReadScopeValue(scope, "row_count") != len(fields["rows"]):
        raise ValueError("writing the count must update the overlay and retain the source")
    if expected_widths is not None:
        widths = [
            ReadScopeValue(scope, "row_count#width"),
            ReadScopeValue(scope, "framework_rows#count#width"),
        ]
        if widths != expected_widths:
            raise ValueError(f"written count widths {widths} differ from {expected_widths}")
    return bytes(writer.OutputValue)


def main():
    parser = ArgumentParser(description="Check independently authored counted archive rows")
    parser.add_argument("mode", choices=("read", "write"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--count-mode")
    parser.add_argument("--expect-widths", type=int, nargs=2)
    options = parser.parse_args()
    rules = ARRAY_FIELDS
    if options.count_mode is not None:
        rules = (replace(rules[0], ModeValue=options.count_mode), *rules[1:])
    if options.mode == "write":
        fields = loads(options.source.read_text(encoding="utf-8"))
        payload = write_record(fields, rules, options.expect_widths)
    else:
        payload = dumps(read_record(options.source.read_bytes(), rules)).encode("utf-8")
    with options.output.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
