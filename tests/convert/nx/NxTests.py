from __future__ import annotations as Annotations

from dataclasses import replace as Replace
from io import BytesIO as BytesIo
from typing import cast as CastValue


from convert.adapters import AdapterRegistry, CadAdapter, ReadOptions, WriteOptions
from typing import Callable
from convert.adapters.nx import NxAdapter, ProbeNx, ReadNx, WriteNx
from convert.adapters.nx.ExprValue import DecodeValue, EncodeValue
from convert.adapters.nx.PayloadBuild import ResizePayload
from convert.adapters.nx.Construction import ConstructMiddle, ObjectCount, Record
from convert.adapters.nx.ExprSection import (
    ExprMiddle,
    ExprLayout,
    ExprObjectCount,
    ExprPreamble,
    PlainSlotCount,
    ValueSlotCount,
    ReadSlotHandle,
    ReadValueSlot,
    SlotObject,
    ValueSlot,
    KMiddleLength as KExprMiddle,
)
from convert.adapters.nx.ObjectSection import (
    AttributeRecord,
    HeadRecord,
    LaneParts,
    LaneRecord,
    RenameView,
    NestingRecord,
    ObjectCount,
    ReadNesting,
    RewriteNesting,
    PairRecord,
    ParseAttribute,
    ParsePair,
    ParseSlots,
    RegToken,
    SlotPrefix,
    SlotRecord,
    FloatWord,
    ReadFloatWord,
    RewriteValues,
    RewriteWordRun,
    ValueWord,
    ViewName,
)
from convert.adapters.nx.RootSection import KRootCounter, PatchAnchor, RootMiddle
from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.Splm import KChecksumOffset, KHeaderRegion
from convert.adapters.nx.SplmBuild import BuildSplm, DirectoryLength
from convert.adapters.nx.SplmReader import ReadSplm
from convert.adapters.nx.HashXxh import HashXxh
from interchange import FeatureKind

# the synthetic payload keeps integration coverage free of vendor saved files
KPartPayload = (
    (0).to_bytes(12, "little")
    + (1).to_bytes(4, "little")
    + (1).to_bytes(4, "little")
    + (24).to_bytes(4, "little")
)

# the synthetic attributes exercise equal length native metadata replacement
KAttributes = (
    b'<?xml version="1.0"?><UgAttributes version="4">'
    b'<Attribute owner="part" title="NX_ReferenceSet" utf8title="NX_ReferenceSet" '
    b'value="Empty" utf8value="Empty" version="3"/>'
    b"</UgAttributes>"
)


# the synthetic trailer reserves the seal slot that nx expects after the header
KTrailer = bytes(0x222)


# a complete modern container proves reader and writer behavior at the file boundary
def SyntheticPart() -> bytes:
    return BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", KPartPayload),
        ],
        [
            ("/Root/UG_PART/LastSavedToggleInfoStream", b"\x01toggle"),
        ],
        FileTag=0x2BBA,
        HeaderTrailer=KTrailer,
    )


# seal positions follow the rebuilt header length and trailer offset
def SealIndex(DataValue: bytes) -> int:
    Parsed = ReadSplm(DataValue)
    HeaderEnd = 0x19 + DirectoryLength(
        [
            (Entry.path, None)
            for Entry in Parsed.entries
            if Entry.region == KHeaderRegion
        ],
        KHeaderRegion,
    )
    return HeaderEnd + KChecksumOffset


# registry discovery must expose the independent reader and writer together
def TestNxDiscovery() -> None:
    Registry = AdapterRegistry()
    _ = Registry.introspect("convert.adapters")
    assert "siemens.nx" in {Adapter.info.format_id for Adapter in Registry.readers()}
    assert "siemens.nx" in {Adapter.info.format_id for Adapter in Registry.writers()}
    assert isinstance(NxAdapter(), CadAdapter)


# probing must accept the modern signature and reject unrelated bytes
def TestNxProbe() -> None:
    assert ProbeNx(SyntheticPart()).confidence == 1.0
    assert ProbeNx(b"not an nx part").confidence == 0.0


# reading must retain native features and project equal length attributes
def TestNxRead() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    assert Document.source.format_id == "siemens.nx"
    assert Document.metadata["nx.container"] == "SPLMSSTR"
    Attributes = CastValue(dict[str, str], Document.metadata["nx.attributes"])
    assert Attributes["NX_ReferenceSet"] == "Empty"
    assert len(Document.feature_timeline) == 1
    assert (
        CastValue(FeatureKind, Document.feature_timeline[0].kind)
        == FeatureKind.KImported
    )
    assert Document.bodies == ()


# writing must rebuild the container and reject header changing edits
def TestNxWrite() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Changed = Replace(
        Document,
        metadata={
            **Document.metadata,
            "nx.attribute_overrides": {"NX_ReferenceSet": "KitNX"},
        },
    )
    Output = BytesIo()
    Result = WriteNx(Changed, Output, WriteOptions())
    assert Result.vendor_loadable is True
    assert Result.application_usable is True
    assert len(Output.getvalue()) == len(SyntheticPart())
    Restored = ReadNx(Output.getvalue(), ReadOptions(strict=False))
    Attributes = CastValue(dict[str, str], Restored.metadata["nx.attributes"])
    assert Attributes["NX_ReferenceSet"] == "KitNX"
    try:
        _ = WriteNx(
            Replace(
                Document,
                metadata={
                    **Document.metadata,
                    "nx.attribute_overrides": {"NX_ReferenceSet": "too long"},
                },
            ),
            BytesIo(),
            WriteOptions(),
        )
    except ValueError as ErrorInfo:
        assert "preserve value byte length" in str(ErrorInfo)
    else:
        raise AssertionError("header changing NX edit was accepted")


# registry writes must preserve the document capability set
def TestNxRegistry() -> None:
    Registry = AdapterRegistry()
    _ = Registry.introspect("convert.adapters")
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Output = BytesIo()
    Result = Registry.WriteDocument(Document, Output, destination_format="siemens.nx")
    assert Result.vendor_loadable is True
    assert Output.getvalue().startswith(b"SPLMSSTR")


# rebuilt containers must carry both native seals after any payload change
def TestNxSeal() -> None:
    DataValue = SyntheticPart()
    Parsed = ReadSplm(DataValue)
    Index = SealIndex(DataValue)
    Stored = int.from_bytes(DataValue[Index : Index + 4], "little")
    assert Stored == HashXxh(DataValue[0x19:Index])
    TailValue = int.from_bytes(DataValue[-4:], "little")
    assert TailValue == HashXxh(DataValue[Parsed.footer_offset : -4])


# stream overrides rebuilt the directory at any payload length and reseal the file
def TestNxOverride() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Longer = KAttributes.replace(b"Empty", b"LongerValue")
    Changed = Replace(
        Document,
        metadata={
            **Document.metadata,
            "nx.stream_overrides": {"/Root/part/attrs": Longer},
        },
    )
    Output = BytesIo()
    Result = WriteNx(Changed, Output, WriteOptions())
    DataValue = Output.getvalue()
    assert Result.bytes_written == len(DataValue)
    assert len(DataValue) > len(SyntheticPart())
    Index = SealIndex(DataValue)
    assert int.from_bytes(DataValue[Index : Index + 4], "little") == HashXxh(
        DataValue[0x19:Index]
    )
    Restored = ReadNx(DataValue, ReadOptions(strict=False))
    Attributes = CastValue(dict[str, str], Restored.metadata["nx.attributes"])
    assert Attributes["NX_ReferenceSet"] == "LongerValue"


# unknown stream overrides must fail instead of disappearing
def TestNxUnknown() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Changed = Replace(
        Document,
        metadata={
            **Document.metadata,
            "nx.stream_overrides": {"/Root/part/missing": b"data"},
        },
    )
    try:
        _ = WriteNx(Changed, BytesIo(), WriteOptions())
    except ValueError as ErrorInfo:
        assert "unknown stream" in str(ErrorInfo)
    else:
        raise AssertionError("unknown NX stream override was accepted")


# empty attribute overrides must not block a valid rewrite
def TestNxEmpty() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Changed = Replace(
        Document,
        metadata={**Document.metadata, "nx.attribute_overrides": {}},
    )
    Result = WriteNx(Changed, BytesIo(), WriteOptions())
    assert Result.vendor_loadable is True


# the index may end before a twelve byte boundary with filler bytes
def TestNxFiller() -> None:
    Payload = (
        (0).to_bytes(12, "little")
        + (1).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (32).to_bytes(4, "little")
        + bytes(8)
    )
    DataValue = BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", Payload),
        ],
        FileTag=0x2BBA,
        HeaderTrailer=KTrailer,
    )
    Document = ReadNx(DataValue, ReadOptions(strict=False))
    assert Document.metadata["nx.segment_count"] == 2


# a same length rename rewrites every native name lane and keeps the part valid
def TestNxRename() -> None:
    import tempfile as TempLib
    from pathlib import Path as PathLib

    Payload = (
        (0).to_bytes(12, "little")
        + (1).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (24).to_bytes(4, "little")
        + b"synth.prt"
    )
    DataValue = BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", Payload),
        ],
        FileTag=0x2BBA,
        HeaderTrailer=KTrailer,
    )
    with TempLib.TemporaryDirectory() as Folder:
        Source = PathLib(Folder) / "synth.prt"
        Target = PathLib(Folder) / "renamed.prt"
        _ = Source.write_bytes(DataValue)
        Document = ReadNx(Source, ReadOptions(strict=False))
        Changed = Replace(
            Document, metadata={**Document.metadata, "nx.part_name": "other.prt"}
        )
        Result = WriteNx(Changed, Target, WriteOptions())
        assert Result.metadata["part_renamed"] is True
        Written = Target.read_bytes()
        assert b"other.prt" in Written
        assert b"synth.prt" not in Written


# rename refuses a different length and a non prt suffix instead of corrupting
def TestNxNoRename() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    for BadName in ("other.prt", "synth.stp"):
        try:
            _ = WriteNx(
                Replace(
                    Document, metadata={**Document.metadata, "nx.part_name": BadName}
                ),
                BytesIo(),
                WriteOptions(),
            )
        except ValueError:
            continue
        raise AssertionError(f"rename accepted {BadName}")


# expression handles must round trip the values nx stores in its records
def TestNxExprValue() -> None:
    for Value in (0.75, 1.0, 2.0, 3.0, 4.5, 6.0, 12.5, 40.0, 100.0, 250.0):
        assert abs(DecodeValue(EncodeValue(Value)) - Value) < 1e-9
    assert EncodeValue(12.5) == 0x4950
    assert EncodeValue(40.0) == 0x6450
    assert EncodeValue(1.0) == 1
    for BadValue in (0.0, -1.0, 0.5):
        try:
            _ = EncodeValue(BadValue)
        except ValueError:
            continue
        raise AssertionError(f"expression encoder accepted {BadValue}")


# the expression value override rewrites the handle in the native record
def TestNxExprWrite() -> None:
    Payload = (
        (0).to_bytes(12, "little")
        + (1).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (40).to_bytes(4, "little")
        + b"sample_expr_record\x00"
        + b"\x82\xc0\x01\x00"
        + EncodeValue(12.5).to_bytes(2, "little")
        + b"\x00\x00"
    )
    DataValue = BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", Payload),
        ],
        FileTag=0x2BBA,
        HeaderTrailer=KTrailer,
    )
    Document = ReadNx(DataValue, ReadOptions(strict=False))
    Changed = Replace(
        Document,
        metadata={**Document.metadata, "nx.expression_values": {"sample": 40.0}},
    )
    import tempfile as TempLib
    from pathlib import Path as PathLib

    with TempLib.TemporaryDirectory() as Folder:
        Target = PathLib(Folder) / "expr.prt"
        Result = WriteNx(Changed, Target, WriteOptions())
        assert Result.metadata["expression_values"] is True
        Written = Target.read_bytes()
        assert b"\x82\xc0\x01\x00" + EncodeValue(40.0).to_bytes(2, "little") in Written


# unknown expressions and unencodable values are refused instead of patched
def TestNxExprGuard() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    for BadValues in ({"missing": 1.0}, {"synthetic": 0.25}):
        try:
            _ = WriteNx(
                Replace(
                    Document,
                    metadata={**Document.metadata, "nx.expression_values": BadValues},
                ),
                BytesIo(),
                WriteOptions(),
            )
        except ValueError:
            continue
        raise AssertionError(f"expression override accepted {BadValues}")


# body length authoring refuses parts without a single measurable solid body
def TestNxBodyGuard() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    for BadLength in (60.0, -5.0):
        try:
            _ = WriteNx(
                Replace(
                    Document,
                    metadata={**Document.metadata, "nx.body_length": BadLength},
                ),
                BytesIo(),
                WriteOptions(),
            )
        except ValueError:
            continue
        raise AssertionError(f"body length accepted {BadLength}")


# feature dimensions are refused because the body would keep the old shape
def TestNxExprDim() -> None:
    Payload = (
        (0).to_bytes(12, "little")
        + (1).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (64).to_bytes(4, "little")
        + b"p1: 30; "
        + b"sample_record\x00"
        + b"\x82\xc0\x01\x00"
        + EncodeValue(30.0).to_bytes(2, "little")
        + b"\x00\x00"
    )
    DataValue = BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", Payload),
        ],
        FileTag=0x2BBA,
        HeaderTrailer=KTrailer,
    )
    Document = ReadNx(DataValue, ReadOptions(strict=False))
    try:
        _ = WriteNx(
            Replace(
                Document,
                metadata={**Document.metadata, "nx.expression_values": {"p1": 45.0}},
            ),
            BytesIo(),
            WriteOptions(),
        )
    except ValueError:
        return
    raise AssertionError("expression override accepted a feature dimension")


# section replacement keeps the segment index consistent when a body changes length
def TestNxResize() -> None:
    def Section(BodyValue: bytes) -> bytes:
        return (
            b"\xff\xff\xff\xff"
            + bytes(4)
            + len(BodyValue).to_bytes(4, "big")
            + BodyValue
        )

    First = b"OM\x01\x01" + b"first body"
    Second = b"OM\x01\x01" + b"second body"
    Blocks = Section(First) + Section(Second)
    Start = 48
    IndexHeader = (1).to_bytes(4, "little") + (1).to_bytes(4, "little")
    IndexRows = (
        IndexHeader
        + (Start).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (Start).to_bytes(4, "little")
        + (3).to_bytes(4, "little")
        + (0).to_bytes(4, "little")
        + (Start + len(Section(First))).to_bytes(4, "little")
    )
    Payload = bytes(12) + IndexRows + Blocks
    Parsed = ReadPayload(Payload)
    assert len(Parsed.sections) == 2
    assert Parsed.sections[0].offset == Start
    Bodies = [
        Payload[SectionValue.body_offset : SectionValue.body_offset + SectionValue.size]
        for SectionValue in Parsed.sections
    ]
    assert Bodies == [First, Second]
    assert ResizePayload(Payload, Bodies) == Payload
    Longer = First + b" and more"
    Grown = ResizePayload(Payload, [Longer, Second])
    Checked = ReadPayload(Grown)
    assert len(Checked.sections) == 2
    assert Checked.sections[0].size == len(Longer)
    assert Checked.sections[1].offset == Start + len(Section(Longer))
    assert (
        Grown[
            Checked.sections[1].body_offset : Checked.sections[1].body_offset
            + Checked.sections[1].size
        ]
        == Second
    )
    try:
        _ = ResizePayload(Payload, [First])
    except ValueError:
        return
    raise AssertionError("section resize accepted a wrong body count")


# the root middle is a fixed layout around one counter and one anchor identity
def TestNxRoot() -> None:
    Middle = RootMiddle(KRootCounter, b"\xff" * 7)
    assert len(Middle) == 176
    assert Middle[0x08:0x0C] == KRootCounter.to_bytes(4, "little")
    assert Middle[0x2C:0x30] == (KRootCounter + 49).to_bytes(4, "little")
    assert Middle[0x30:0x34] == (KRootCounter + 76).to_bytes(4, "little")
    assert Middle[0x7B:0x7E] == b"\xe0\x6a\xf8"
    assert Middle[0x7E:0x85] == b"\xff" * 7
    assert b"NX 2506.9120 - External User Function" in Middle
    assert Middle.endswith(b"\x01\x01")
    Other = RootMiddle(0x1E7, b"\xff" * 7)
    assert Other[0x08:0x0C] == (0x1E7).to_bytes(4, "little")
    assert Other[0x2C:0x30] == (0x1E7 + 49).to_bytes(4, "little")
    assert Other[0x30:0x34] == (0x1E7 + 76).to_bytes(4, "little")
    try:
        _ = RootMiddle(0, b"\xff" * 7)
    except ValueError:
        pass
    else:
        raise AssertionError("root middle accepted a zero counter")


# authored sections need a payload that carries a root and a feature section
def TestNxAuth() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    try:
        _ = WriteNx(
            Replace(
                Document,
                metadata={**Document.metadata, "nx.author_sections": True},
            ),
            BytesIo(),
            WriteOptions(),
        )
    except ValueError:
        return
    raise AssertionError("authored sections accepted a payload without sections")


# the body less construction middle is a fixed 356 byte layout
def TestNxConstr() -> None:
    Middle = ConstructMiddle(0x34C)
    assert len(Middle) == 356
    assert int.from_bytes(Middle[0x2C:0x30], "little") == 0x3D8
    assert Middle[0xCA:0xD1] == b"\xff" * 7
    Table = [
        int.from_bytes(Middle[0x70 + 4 * Index : 0x74 + 4 * Index], "little")
        for Index in range(3)
    ]
    assert Table == [0x34C + 0xBD, 0x34C + 0xD8, 0x34C + 0xF4]
    assert Middle[0xBD:0xC7] == b"\x41\x00\x03\x05\x01\x00\x04\x05\x02\x00"
    Framed = ConstructMiddle(0x34C, b"\xff" * 7, 0x3DC)
    assert int.from_bytes(Framed[0x2C:0x30], "little") == 0x3DC
    assert len(Record()) == 112
    assert Record()[0x20] == 7 and Record()[0x43] == 8
    assert Record(10, 11)[0x20] == 10 and Record(10, 11)[0x43] == 11
    try:
        _ = ConstructMiddle(0x34C, b"\xff" * 6)
    except ValueError:
        pass
    else:
        raise AssertionError("construction middle accepted a short identity")
    assert (
        ObjectCount(
            (0x29).to_bytes(0, "little")
            + bytes(0x25)
            + (9).to_bytes(4, "little")
            + b"dim40.prt"
            + (3).to_bytes(4, "little")
            + bytes(28)
        )
        == 3
    )


# every section anchors its saved state on one identity after the anchor marker
def TestNxAnchor() -> None:
    SectionBody = b"\x00" * 9 + b"\xe0\x6a\xf8" + b"\x01" * 7 + b"\x00" * 4
    Patched = PatchAnchor(SectionBody)
    assert Patched[12:19] == b"\xff" * 7
    assert Patched[:12] == SectionBody[:12]
    assert Patched[19:] == SectionBody[19:]
    try:
        _ = PatchAnchor(b"\x00" * 20)
    except ValueError:
        pass
    else:
        raise AssertionError("anchor patch accepted a body without an anchor")
    try:
        _ = PatchAnchor(SectionBody, b"\xff" * 6)
    except ValueError:
        return
    raise AssertionError("anchor patch accepted a short identity")


# the expression section of a part without expressions is a fixed six object layout
def TestNxExpr() -> None:
    Middle = ExprMiddle(0)
    assert len(Middle) == KExprMiddle == 337
    assert int.from_bytes(Middle[0x0D:0x11], "little") == 0x79
    Table = [
        int.from_bytes(Middle[0x45 + 4 * Index : 0x49 + 4 * Index], "little")
        for Index in range(6)
    ]
    assert Table == [0xAA, 0xC5, 0xDF, 0x121, 0x125, 0x13B]
    assert int.from_bytes(Middle[0x5D:0x61], "little") == 6
    assert Middle[0x79:0x7C] == b"\x03\x01\x27"
    assert Middle[0xAA:0xB4] == b"\x41\x00\x03\x05\x01\x00\x04\x05\x02\x00"
    AnchorAt = Middle.find(b"\xe0\x6a\xf8")
    assert Middle[AnchorAt + 3 : AnchorAt + 10] == b"\xff" * 7
    assert Middle.endswith(b"\x00\x3f\x00\x00")
    try:
        _ = ExprMiddle(0, b"\xff" * 6)
    except ValueError:
        return
    raise AssertionError("expression middle accepted a short identity")


# the root head record is a tag a length prefixed text and a fixed tail
def CheckHeadRecord(PartText: bytes) -> None:
    Record = HeadRecord(PartText)
    assert Record[:4] == b"\x41\x00\x03\x03"
    assert Record[4] == len(PartText) + 2
    assert Record[5 : 5 + len(PartText)] == PartText
    assert Record[5 + len(PartText)] == 0
    AnchorAt = Record.find(b"\xe0\x6a\xf8")
    assert AnchorAt > 0
    assert Record[AnchorAt + 3 : AnchorAt + 10] == b"\xff" * 7
    try:
        _ = HeadRecord(b"")
    except ValueError:
        pass
    else:
        raise AssertionError("head record accepted an empty text")
    try:
        _ = HeadRecord(PartText, b"\xff" * 6)
    except ValueError:
        return
    raise AssertionError("head record accepted a short identity")


# the root head record is a tag a length prefixed text and a fixed tail
def TestNxObject() -> None:
    CheckHeadRecord(b'Part renamed from "C:\\kit\\part.prt"')
    CheckHeadRecord(b"x" * 40)
    Header = bytearray(0x29 + 9 + 32 + 4)
    Header[0x25:0x29] = (9).to_bytes(4, "little")
    Header[0x29 + 9 : 0x29 + 9 + 4] = (214).to_bytes(4, "little")
    assert ObjectCount(bytes(Header)) == 214
    Header[0x29 + 9 : 0x29 + 9 + 4] = bytes(4)
    try:
        _ = ObjectCount(bytes(Header))
    except ValueError:
        return
    raise AssertionError("object count accepted zero objects")


# two root object record families read back as the fields they are written from
def TestNxGrammar() -> None:
    for KeyText, ValueText, Ordinal, Marker in (
        (b"X", b"", 0x2F, 1),
        (b"CBORE<o> ", b"", 0x32, 1),
        (b"-", b" DEEP", 0x31, 1),
        (b"Major:<o> ", b"", 0x10, 0),
        (b"", b"", 0x16, 0),
    ):
        Record = AttributeRecord(KeyText, ValueText, Ordinal, Marker)
        assert ParseAttribute(Record) == (KeyText, ValueText, Ordinal, Marker)
    for First, Second in ((0x6F, 0x70), (0x64, 0x65), (0xA6, 0xA7), (0x0A, 0x0B)):
        Record = PairRecord(First, Second)
        assert ParsePair(Record) == (First, Second)
    assert RegToken(0x6F) == b"\x6f"
    assert RegToken(0xA6) == b"\x80\xa6"
    assert RegToken(0x1A6) == b"\x81\xa6"
    Guards: tuple[Callable[[], object], ...] = (
        lambda: AttributeRecord(b"x" * 254, b"", 0),
        lambda: PairRecord(-1, 0),
    )
    for Guard in Guards:
        try:
            _ = Guard()
        except ValueError:
            continue
        raise AssertionError("record grammar accepted an out of range value")
    for Malformed in (b"\x01\x02\x04\x02\x00", b"\x03\x11\x00"):
        try:
            _ = ParseAttribute(Malformed) if Malformed[0] == 1 else ParsePair(Malformed)
        except ValueError:
            continue
        raise AssertionError("record grammar accepted a malformed record")


# a neutral document is refused with a message that states the supported scope
def TestNxNeutral() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    try:
        _ = WriteNx(Document, BytesIo(), WriteOptions())
    except ValueError as ErrorInfo:
        assert "retained native NX document" in str(ErrorInfo)
        assert "not supported" in str(ErrorInfo)
        return
    raise AssertionError("a neutral document was accepted for NX writing")


# a slot record frames a list of occupied and empty registry slots
def TestNxSlots() -> None:
    Tokens: tuple[int | None, ...] = (0x31, None, 0x43, None, 0x32)
    Frame = bytes.fromhex("02024100364104010111")
    Record = SlotRecord(Frame, Tokens)
    assert Record[:10] == bytes.fromhex("02024100364104010111")
    assert len(Record) == 10 + 3 * 2 + 2
    assert ParseSlots(Record) == Tokens
    assert ParseSlots(SlotRecord(Frame, (None, None))) == (None, None)
    assert SlotRecord(Frame, (None, None))[10:] == b"\xff\xff"
    ReversedTokens: tuple[int | None, ...] = tuple(reversed(Tokens))
    assert len(SlotRecord(Frame, ReversedTokens)) == len(Record)
    PartFrame = bytes.fromhex("0202ff00363204010111") + b"\xff" * 3
    assert SlotPrefix(PartFrame) == bytes.fromhex("0202ff00363204010111")
    try:
        _ = ParseSlots(bytes.fromhex("0202410036410401011100"))
    except ValueError:
        pass
    else:
        raise AssertionError("slot grammar accepted an unknown token")
    try:
        _ = SlotRecord(Frame, (0x100,))
    except ValueError:
        return
    raise AssertionError("slot grammar accepted an out of range slot")


# a lane record names a count a flag run a mask and a list of slot tokens
def TestNxLane() -> None:
    Record = bytes.fromhex(
        "0311030111"
        + "01" * 9
        + "02"
        + "01" * 9
        + "02"
        + "e0"
        + "55559556"
        + "0111"
        + "6f"
        + "ff" * 6
        + "70"
        + "ff" * 8
    )
    Count, Flags, MaskValue, Tokens = LaneParts(Record)
    assert Count == 3
    assert len(Flags) == 19
    assert MaskValue == bytes.fromhex("55559556")
    assert Tokens == (
        b"\x6f",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\x70",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
        b"\xff",
    )
    assert LaneRecord(Count, Flags, MaskValue, Tokens) == Record
    TextRecord = LaneParts(
        bytes.fromhex(
            "0611060111"
            + "01" * 3
            + "040102"
            + "01" * 4
            + "0501030102"
            + "e0"
            + "66559956"
            + "0111"
            + "0307"
            + "2054485255"
            + "00"
        )
    )
    assert TextRecord[0] == 6 and TextRecord[3][0] == bytes.fromhex("0307205448525500")
    for Malformed in (b"", bytes(12), Record[:-1] + b"\x00"):
        try:
            _ = LaneParts(Malformed)
        except ValueError:
            continue
        raise AssertionError("lane grammar accepted a malformed record")
    try:
        _ = LaneRecord(3, b"\x01", b"\x00\x00\x00", ())
    except ValueError:
        return
    raise AssertionError("lane grammar accepted a short mask")


# a named view record carries its name as a length prefixed text token
def TestNxView() -> None:
    Record = b"\x02\x02\x41\x41" + bytes(10) + b"\x03\x07Front\x00" + bytes(20)
    assert ViewName(Record) == (b"Front", 14, 7)
    assert RenameView(Record, b"Front") == Record
    assert RenameView(Record, b"Baack")[16:21] == b"Baack"
    try:
        _ = RenameView(Record, b"Fron")
    except ValueError:
        pass
    else:
        raise AssertionError("view rename accepted a different name length")
    try:
        _ = ViewName(b"\x02\x02\x41\x41" + bytes(8))
    except ValueError:
        return
    raise AssertionError("view name read a record without a name")


# the numeric words in the token family are expression handles padded to four bytes
def TestNxWord() -> None:
    assert ValueWord(100.0) == bytes.fromhex("50790000")
    assert ValueWord(50.0) == bytes.fromhex("50690000")
    assert ValueWord(20.0) == bytes.fromhex("50540000")
    assert ValueWord(5.0) == bytes.fromhex("50340000")
    try:
        _ = ValueWord(0.5)
    except ValueError:
        return
    raise AssertionError("value word accepted a value below the encoding limit")


# a float word is a single precision value widened to a double with a shifted top byte
def TestNxFloat() -> None:
    assert FloatWord(360.0) == bytes.fromhex("3076800000000000")
    assert FloatWord(0.2) == bytes.fromhex("2fc99999a0000000")
    assert ReadFloatWord(bytes.fromhex("3076800000000000")) == 360.0
    assert abs(ReadFloatWord(bytes.fromhex("2fc99999a0000000")) - 0.2) < 1e-7
    assert ReadFloatWord(bytes.fromhex("2fe8")) == 0.75
    try:
        _ = ReadFloatWord(b"")
    except ValueError:
        return
    raise AssertionError("float word reader accepted an empty word")


# token family words are rewritten from decoded values
def TestNxValues() -> None:
    Record = (
        b"\x02\x02\x41\x00"
        + b"\x35\x06"
        + bytes(8)
        + ValueWord(100.0) * 2
        + FloatWord(360.0)
        + ValueWord(100.0)
        + bytes(2)
    )
    Frame = bytes(12) + Record + bytes(12)
    assert RewriteWordRun(Record, 14, len(Record)) == Record
    Shifted = bytearray(Frame)
    Shifted[0x14:0x18] = ValueWord(100.0)
    assert RewriteValues(bytes(Shifted))


# a block part adds five property slots and one record for each expression
def TestNxExprCount() -> None:
    assert ExprObjectCount(0) == 6
    assert ExprObjectCount(3) == 24
    assert ExprObjectCount(6) == 42
    assert ValueSlotCount(3) == 5 and ValueSlotCount(6) == 11
    assert PlainSlotCount(3) == 10 and PlainSlotCount(6) == 19
    assert ExprObjectCount(3) == 6 + ValueSlotCount(3) + PlainSlotCount(3) + 3
    try:
        _ = ExprObjectCount(-1)
    except ValueError:
        return
    raise AssertionError("expression inventory accepted a negative count")


# an expression property slot is a fixed frame a handle and a terminator
def TestNxSlot() -> None:
    Object = SlotObject(0x0050)
    assert len(Object) == 18
    assert Object[:8] == bytes.fromhex("02020000ff000021")
    assert Object[8:14] == bytes([1]) * 5 + bytes(1)
    assert Object[14:17] == b"\x50\x00\x00"
    assert Object[17] == 0xFF
    assert ReadSlotHandle(Object) == 0x0050
    Guards: tuple[Callable[[], object], ...] = (
        lambda: SlotObject(-1),
        lambda: SlotObject(0x1000000),
    )
    for Guard in Guards:
        try:
            _ = Guard()
        except ValueError:
            continue
        raise AssertionError("slot object accepted an out of range handle")
    try:
        _ = ReadSlotHandle(bytes(17))
    except ValueError:
        return
    raise AssertionError("slot reader accepted a short object")


# a value slot carries the expression value instead of a handle
def TestNxValueSlot() -> None:
    Object = ValueSlot(40.0)
    assert len(Object) == 21
    assert Object[14:18] == bytes.fromhex("50640000")
    assert Object[-1] == 0xFF
    assert ReadValueSlot(Object) == 0x6450
    try:
        _ = ReadValueSlot(Object[:18])
    except ValueError:
        return
    raise AssertionError("value slot reader accepted an 18 byte object")


# the nesting record is a frame segments of leaves and a terminator
def TestNxNest() -> None:
    Record = (
        bytes.fromhex("0202ff005f010401")
        + b"\x03"
        + b"\x01" * 3
        + b"\x11"
        + b"\x01" * 2
        + b"\x02\x02"
    )
    Segments = ReadNesting(Record)
    assert Segments == ((0x03, 3), (0x11, 2))
    assert NestingRecord(Segments) == Record
    Canonical = RewriteNesting(bytes(len(Record) - len(Record)) + Record)
    assert Canonical == Record.replace(b"\x11", b"\x03")


# the writer chooses the object layout rather than reproducing the source order
def TestNxLayout() -> None:
    assert len(ExprLayout(0)) == 6
    for Dimensions in (1, 2, 3, 6):
        Layout = ExprLayout(Dimensions)
        assert len(Layout) == ExprObjectCount(Dimensions)
        assert Layout.count("value") == ValueSlotCount(Dimensions)
        assert Layout.count("plain") == PlainSlotCount(Dimensions)
        assert Layout.count("record") == Dimensions


# the preamble counts objects then runs flags whose length depends on the shape
def TestNxPreamble() -> None:
    Small = ExprPreamble(6, 0x2E1)
    assert Small[:7] == bytes([2]) * 7
    assert Small[7:9] == bytes([1, 1])
    assert Small[9:13] == bytes([1]) * 4
    assert Small[13:17] == (0x2E1).to_bytes(4, "little")
    Large = ExprPreamble(24, 0x40F, 0x55C)
    assert Large[7:9] == bytes([24 - 5, 4])
    assert Large[9:16] == bytes([1]) * 7
    assert Large[16:20] == (0x40F).to_bytes(4, "little")
    assert Large[48:52] == (0x55C).to_bytes(4, "little")
    try:
        _ = ExprPreamble(3, 1)
    except ValueError:
        return
    raise AssertionError("preamble accepted fewer than six objects")
