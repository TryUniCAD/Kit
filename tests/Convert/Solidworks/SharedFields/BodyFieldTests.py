from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut

# neighboring fields expose framing drift and skipped or extra bytes
KBareRules = (
    NativeField("Boolean", "flag", "i32"),
    NativeField("Bytes", "fixed", MaskValue=16),
    NativeField(
        "GhostCount", "ghost_count", OtherName="ghost_flags", CountValue="ghost_rows"
    ),
    NativeField(
        "Section",
        "",
        BodyValue=(
            NativeField(
                "Array",
                "rows",
                "Split",
                BodyValue=(NativeField("Scalar", "value", "i32"),),
                CountValue="high",
                OtherName="low",
                ModeValue="Unsigned",
            ),
        ),
    ),
    NativeField("BBoxCache", "bounds"),
    NativeField("MassCaches", "mass", OtherName="selector"),
    NativeField("Scalar", "after", "i32"),
)


# native body fields must retain their values after emission and independent graph readback
def TestBodyFields() -> None:
    ClassValue = RuntimeClass("FieldProbe", 1)
    ContextValue = BodyContext(
        KHeaderVersion, {"FieldProbe": KBareRules}, {}, {"FieldProbe": (1,)}
    )
    Fields: dict[str, object] = {
        "flag": 1,
        "flag#wire": -4,
        "fixed": bytes(range(16)),
        "ghost_rows": [],
        "ghost_flags": -8,
        "rows": [{"value": -37}],
        "high": 2,
        "low": 1,
        "bounds": [],
        "mass": [],
        "selector": 0,
        "after": -77,
    }
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, ArchiveNode(ClassValue, Fields))
    Cursor = BinaryReader(bytes(WriterValue.OutputValue))
    ReadContext = BodyContext(
        KHeaderVersion, {"FieldProbe": KBareRules}, {}, {"FieldProbe": (1,)}
    )
    ReaderValue = GraphReader(
        Cursor, ArchiveMaps(1), PartialValue(ReadBodyMut, ReadContext)
    )
    Decoded = ReadNodeMut(ReaderValue)
    assert Decoded is not None
    assert Decoded.ClassValue == ClassValue
    assert not Cursor.GetRemaining()
    for FieldName in Fields.keys() - {"ghost_rows"}:
        assert Decoded.FieldsValue[FieldName] == Fields[FieldName]
    assert Decoded.FieldsValue["ghost_count"] == 0
