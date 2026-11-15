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
    ExprMiddleDim,
    ExprLayout,
    ExprObjectCount,
    ExprHeadTail,
    ExprLane,
    ReadLane,
    ExprOccupancy,
    OccupancyFrame,
    OccupancyMap,
    ExprPreamble,
    GroupPair,
    GroupRecord,
    ReadGroupValues,
    PlainSlotCount,
    ValueSlotCount,
    ReadSlotHandle,
    ReadValueSlot,
    SlotObject,
    ValueSlot,
    KMiddleLength as KExprMiddle,
)
from convert.adapters.nx.ClassEntry import ClassLink, EntryParts, NameDigest
from convert.adapters.nx.LegacySection import ReadSections
from convert.adapters.nx.LegacyObject import ReadIndex, ReadObjects, ReadRecords
from convert.adapters.nx.ClassTable import (
    ReadRegistry,
    ReadToken,
    WriteRegistry,
    WriteToken,
)
from convert.adapters.nx.LegacyClasses import (
    ClassTableEnd,
    LegacyAttrs,
    LegacyCodes,
    LegacyTable,
    ReadFrame,
)
from convert.adapters.nx.ObjectSection import (
    AttributeRecord,
    CarryId,
    HeadRecord,
    HeadSuffix,
    KHeadSuffix,
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

    # needed so the resize test builds one section body without repeating framing
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
        _ = HeadRecord(PartText, b"\xff" * 5)
    except ValueError:
        pass
    else:
        raise AssertionError("head record accepted a short identity")
    assert HeadRecord(PartText, b"\xff" * 6)[AnchorAt + 3 : AnchorAt + 9] == b"\xff" * 6
    assert HeadSuffix(214) == KHeadSuffix
    assert HeadSuffix(251) == bytes.fromhex(
        "80fa021304050100010180fa021380fb020000"
    )


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

    # needed so every rejected attribute record is exercised in one ordered list
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

    # needed so every rejected slot object is exercised in one ordered list
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


# the default group pair is the same object in every expression section
def TestNxGroup() -> None:
    PairBytes = GroupPair()
    assert len(PairBytes) == 37
    assert PairBytes[:9] == bytes.fromhex("0202010241040f") + b"De"
    assert PairBytes.count(b"Default Group") == 2
    assert PairBytes == bytes.fromhex(
        "0202010241040f44656661756c742047726f757000"
    ) + bytes.fromhex("040f44656661756c742047726f757000")


# a group value is a length byte a text and a terminator
def TestNxGroupList() -> None:
    assert GroupRecord(()) == bytes.fromhex(
        "0202040f"
    ) + b"Default Group\x00" + bytes.fromhex("003f0000")
    Single = GroupRecord((b"50",))
    assert Single[-4:] == bytes.fromhex("04353000")
    assert ReadGroupValues(Single) == (b"50",)
    SeveralValues = GroupRecord((b"1", b"0.5"))
    assert SeveralValues[-5:] == bytes.fromhex("05302e3500")
    assert ReadGroupValues(SeveralValues) == (b"1", b"0.5")
    assert ReadGroupValues(GroupRecord(())) == ()
    try:
        _ = GroupRecord((b"",))
    except ValueError:
        return
    raise AssertionError("group record accepted an empty value")


# the head tail names two ids that follow the last one
def TestNxHeadTail() -> None:
    assert ExprHeadTail(6, 0) == bytes.fromhex("08021309020000")
    assert ExprHeadTail(24, 3) == bytes.fromhex("1d02131e020000")
    assert ExprHeadTail(42, 6) == bytes.fromhex("32021333020000")
    assert ExprHeadTail(25, 3) == bytes.fromhex("1e02131f020000")
    try:
        _ = ExprHeadTail(5, 0)
    except ValueError:
        return
    raise AssertionError("head tail accepted fewer than six objects")


# the names lane places its tokens from the first slot and fills out the maps
def TestNxLaneMap() -> None:
    Labels = (b"\x8c\x00", b"\x8c\x01", b"\x8c\x02")
    LaneBytes = ExprLane(Labels, bytes.fromhex("535455"))
    assert len(LaneBytes) == 135
    assert LaneBytes[0] == 4
    assert b"EXP_lookup_exp" in LaneBytes
    assert LaneBytes[-2:] == bytes.fromhex("0421")
    assert ReadLane(LaneBytes) == (Labels, bytes.fromhex("535455"))
    WideToken = ExprLane((b"\xe0\x66\x05\x90\xfd",), b"\x53")
    assert len(WideToken) == 136
    assert ReadLane(WideToken)[0] == (b"\xe0\x66\x05\x90\xfd",)
    try:
        _ = ExprLane(Labels, b"\x53")
    except ValueError:
        return
    raise AssertionError("names lane accepted a value count mismatch")


# the occupancy object lists the allocated ids a dimension shape adds
def TestNxOccupancy() -> None:
    Three = ExprOccupancy(3)
    assert len(Three) == 37
    assert Three[:3] == bytes.fromhex("100121")
    assert Three[-2:] == bytes.fromhex("1021")
    assert Three[3:5] == bytes.fromhex("4344")
    assert Three[18] == 0x51
    assert Three.count(0xFF) == 17
    assert len(ExprOccupancy(6)) == 69
    assert ExprOccupancy(6)[:3] == bytes.fromhex("1f0141")
    assert len(ExprOccupancy(9)) == 69
    assert ExprOccupancy(9)[:3] == bytes.fromhex("2e0141")
    assert ExprOccupancy(3, 2)[-2:] == bytes.fromhex("1221")
    try:
        _ = ExprOccupancy(0)
    except ValueError:
        return
    raise AssertionError("occupancy accepted zero dimensions")


# the occupancy frame follows the dimension count and the continuation count
def TestNxOccFrames() -> None:
    assert OccupancyFrame(3, 0) == (bytes.fromhex("100121"), bytes.fromhex("1021"))
    assert OccupancyFrame(6, 3) == (bytes.fromhex("1f0141"), bytes.fromhex("2241"))
    assert OccupancyMap(9) == 64


# a dimension shape composes the nine objects between a fixed table and its records
def TestNxMiddleDim() -> None:
    LaneBytes = ExprLane(
        (b"\x8c\x00", b"\x8c\x01", b"\x8c\x02"), bytes.fromhex("535455")
    )
    Slots = tuple(ValueSlot(40.0 + Index) for Index in range(5)) + tuple(
        SlotObject(Index) for Index in range(10)
    )
    Built = ExprMiddleDim(
        0x2F7,
        3,
        bytes(7),
        (b"\x8c\x00", b"\x8c\x01", b"\x8c\x02"),
        bytes.fromhex("535455"),
        (b"40", b"20"),
        Slots,
        (b"\x01" * 48,) * 3,
    )
    assert len(LaneBytes) == 135
    assert Built[0] == 2
    assert len(Built) > 900
    assert Built[0x54 : 0x54 + 4] == (0x2F7 + 0x149).to_bytes(4, "little")
    Order = Built[0x54 + 4 * 24 :]
    assert int.from_bytes(Order[0:4], "little") == 24
    assert int.from_bytes(Order[4:8], "little") == 1


# the carry id descends per block and shifts with the block count and ordinal
def TestNxCarry() -> None:
    assert CarryId(1, 0, 19) == 57
    assert CarryId(1, 0, 30) == 46
    assert CarryId(2, 0, 32) == 50
    assert CarryId(2, 1, 44) == 39
    assert CarryId(3, 2, 69) == 21
    try:
        _ = CarryId(1, 1, 19)
    except ValueError:
        return
    raise AssertionError("carry id accepted a block outside the block count")


# the name digest is xxh32 over the chain schema class and kind triples
def TestNxClassLink() -> None:
    MetaSchema = "UGS::OM::Meta"
    RootChain: tuple[ClassLink, ...] = (
        ClassLink(MetaSchema, "UGS::OM::MethodicObject", 1),
        ClassLink(MetaSchema, "UGS::OM::StorableObject", 1),
        ClassLink(MetaSchema, "UGS::OM::TaggedObject", 1),
        ClassLink(MetaSchema, "UGS::OM::RootObject", 1),
    )
    assert NameDigest(RootChain) == 0xFEA54BB0
    PartChain: tuple[ClassLink, ...] = RootChain[:3] + (
        ClassLink(MetaSchema, "UGS::OM::VersionedObject", 1),
        ClassLink("UGS::RM", "UGS::RM_part", 47),
    )
    assert NameDigest(PartChain) == 0xE4F7C08F
    PointChain: tuple[ClassLink, ...] = (
        ClassLink(MetaSchema, "UGS::OM::MethodicObject", 1),
        ClassLink(MetaSchema, "UGS::OM::StorableObject", 1),
        ClassLink(MetaSchema, "UGS::OM::TaggedObject", 1),
        ClassLink(MetaSchema, "UGS::OM::VersionedObject", 1),
        ClassLink("UGS::RM", "UGS::RM_entity", 47),
        ClassLink("UGS::RM", "UGS::RM_displayable_entity", 47),
        ClassLink("UGS::SO", "UGS::SO", 18),
        ClassLink("UGS::POINT", "UGS::POINT", 64),
    )
    assert NameDigest(PointChain) == 0x179C7E0E
    Entry = bytes.fromhex("3874b04ba5fe911bf67902")
    assert EntryParts(Entry, 0xFEA54BB0) == (bytes.fromhex("3874"), 0x79F61B91, 0x02)
    try:
        _ = NameDigest(())
    except ValueError:
        return
    raise AssertionError("name digest accepted an empty chain")


# a legacy payload carries type six frames of schema class and value
def TestNxLegacy() -> None:

    # needed so the legacy frame test builds one class frame without repeating bytes
    def Frame(
        SchemaText: str, SchemaFlag: int, ClassName: str, ClassValue: int
    ) -> bytes:
        return (
            b"\x06"
            + len(SchemaText).to_bytes(2, "little")
            + SchemaText.encode("ascii")
            + SchemaFlag.to_bytes(4, "little")
            + len(ClassName).to_bytes(2, "little")
            + ClassName.encode("ascii")
            + ClassValue.to_bytes(4, "little")
        )

    # needed so the legacy field test builds one attribute frame without repeating bytes
    def Field(
        SchemaText: str,
        SchemaFlag: int,
        ClassName: str,
        FieldName: str,
        FieldValue: int,
    ) -> bytes:
        return (
            b"\x07"
            + len(SchemaText).to_bytes(2, "little")
            + SchemaText.encode("ascii")
            + SchemaFlag.to_bytes(4, "little")
            + len(ClassName).to_bytes(2, "little")
            + ClassName.encode("ascii")
            + len(FieldName).to_bytes(2, "little")
            + FieldName.encode("ascii")
            + FieldValue.to_bytes(4, "little")
        )

    PayloadHead = (
        b"\x00\x10padding" * 3 + (7).to_bytes(2, "little") + (9).to_bytes(2, "little")
    )
    PayloadBytes = (
        PayloadHead
        + Frame("UGS::OM::Meta", 1, "UGS::OM::RootObject", 55)
        + Frame("RM", 40, "UGS::RM_part", 100)
        + Field("UGS::OM::Meta", 1, "UGS::OM::RootObject", "first_record_area", 207)
        + b"\x00tail"
    )
    Records = LegacyTable(PayloadBytes)
    assert len(Records) == 2
    assert Records[0].Schema == "UGS::OM::Meta"
    assert Records[0].SchemaFlag == 1
    assert Records[0].Name == "UGS::OM::RootObject"
    assert Records[0].Value == 55
    assert Records[1].Schema == "RM"
    assert Records[1].Value == 100
    assert LegacyCodes(PayloadBytes) == (7, 9)
    Start = len(PayloadHead)
    assert ClassTableEnd(PayloadBytes, Records) == Start + len(
        Frame("UGS::OM::Meta", 1, "UGS::OM::RootObject", 55)
    ) + len(Frame("RM", 40, "UGS::RM_part", 100))
    Fields = LegacyAttrs(PayloadBytes)
    assert len(Fields) == 1
    assert Fields[0].Schema == "UGS::OM::Meta"
    assert Fields[0].ClassName == "UGS::OM::RootObject"
    assert Fields[0].Attribute == "first_record_area"
    assert Fields[0].Value == 207
    assert ReadFrame(PayloadBytes, len(PayloadBytes) - 1) is None
    try:
        _ = LegacyTable(b"no classes here")
    except ValueError:
        return
    raise AssertionError("legacy parser accepted a payload without a class table")


# a legacy payload holds length prefixed object model sections
def TestNxSections() -> None:

    # needed so the section test builds one length prefixed section without repeating bytes
    def Build(VersionValue: int, PlatformText: str, PartText: str) -> bytes:
        SectionBytes = (
            b"OM\x01\x01"
            + VersionValue.to_bytes(4, "big")
            + (0x25).to_bytes(4, "big")
            + bytes(4)
            + bytes([1, 2, 3])
            + len(PlatformText).to_bytes(4, "little")
            + PlatformText.encode("ascii")
            + len(PartText).to_bytes(4, "little")
            + PartText.encode("ascii")
            + b"".join(
                Value.to_bytes(4, "little") for Value in (7, 1, 0, 3, 0, 0, 9, 9)
            )
        )
        return len(SectionBytes).to_bytes(4, "big") + SectionBytes

    PayloadBytes = Build(7, "Intel x86/Windows NT", "authored.prt") + bytes(8)
    Sections = ReadSections(PayloadBytes)
    assert len(Sections) == 1
    assert Sections[0].Version == 7
    assert Sections[0].KindValue == 0x25
    assert Sections[0].Platform == "Intel x86/Windows NT"
    assert Sections[0].PartName == "authored.prt"
    assert Sections[0].Counts == (7, 1, 0, 3, 0, 0, 9, 9)
    assert Sections[0].Offset == 4
    assert Sections[0].Length == len(PayloadBytes) - 12
    assert ReadSections(b"no sections at all") == ()


# a legacy object area is framed by a monotone index and a count prefixed table
def TestNxFrame() -> None:
    Platform = "Intel x86/Windows NT"
    PartName = "authored.prt"
    SectionBytes = (
        b"OM\x01\x01"
        + (7).to_bytes(4, "big")
        + (0x25).to_bytes(4, "big")
        + bytes(4)
        + bytes([1, 2, 3])
        + len(Platform).to_bytes(4, "little")
        + Platform.encode("ascii")
        + len(PartName).to_bytes(4, "little")
        + PartName.encode("ascii")
        + b"".join(Value.to_bytes(4, "little") for Value in (7, 1, 0, 3, 0, 0, 9, 9))
    )
    Offset = 4
    BodyBase = Offset + len(SectionBytes)
    ObjectEnd = BodyBase + 4 * 4 + 4 + 4 * 3
    Entries = (0, ObjectEnd - Offset, ObjectEnd - Offset + 12, ObjectEnd - Offset + 24)
    Records = b"a" * 12 + b"b" * 12 + b"c" * 12
    BodyValue = (
        SectionBytes
        + b"".join(Value.to_bytes(4, "little") for Value in Entries)
        + len((1, 3, 5)).to_bytes(4, "little")
        + b"".join(Value.to_bytes(4, "little") for Value in (1, 3, 5))
        + Records
    )
    PayloadBytes = len(BodyValue).to_bytes(4, "big") + BodyValue
    Sections = ReadSections(PayloadBytes)
    assert len(Sections) == 1
    Index = ReadIndex(PayloadBytes, Sections[0])
    assert Index is not None
    assert Index.Entries == Entries
    assert Index.Count == 3
    assert Index.ObjectEnd == ObjectEnd
    assert ReadObjects(PayloadBytes, Index) == (1, 3, 5)
    Bounds = ReadRecords(PayloadBytes, Sections[0], Index)
    assert len(Bounds) == 2
    assert Bounds[0].Offset == ObjectEnd
    assert Bounds[0].Length == 12
    assert Bounds[0].ObjectId == 1
    assert Bounds[1].Offset == ObjectEnd + 12
    assert Bounds[1].Length == 12
    assert Bounds[1].ObjectId == 3
    assert ReadIndex(b"no index at all", Sections[0]) is None


# a modern type registry is a reference list a class region and a member region
def TestNxTypeReg() -> None:

    # needed so the registry test builds one token without repeating the width rules
    def Token(Value: int) -> bytes:
        if Value < 0x80:
            return bytes([Value])
        if Value <= 0x1000:
            return bytes([0x80 + (Value - 1) // 256, (Value - 1) % 256])
        return bytes(
            [0xA0 | ((Value - 1) >> 16), ((Value - 1) >> 8) & 0xFF, (Value - 1) & 0xFF]
        )

    # needed so the registry test builds one declaration without repeating the length byte
    def NameBytes(TextValue: str) -> bytes:
        return bytes([len(TextValue) + 1]) + TextValue.encode("ascii")

    assert ReadToken(bytes([0x83, 0xE8]), 0) == (1001, 2)
    assert ReadToken(bytes([0xFF]), 0) == (None, 1)
    References = (
        NameBytes("UGS::OM::Meta")
        + bytes([2])
        + NameBytes("UGS::RM")
        + bytes([0x30])
        + bytes([0x01])
    )
    Classes = (
        NameBytes("UGS::OM::RootObject")
        + Token(56)
        + Token(120)
        + bytes.fromhex("b04ba5fe911bf679")
        + Token(2)
        + NameBytes("UGS::RM_part")
        + Token(101)
        + Token(123)
        + bytes.fromhex("8fc0f7e4255a70c8")
        + Token(1)
        + bytes([0x02])
    )
    Members = NameBytes("first_record_area") + Token(208) + Token(28)
    Payload = References + Classes + Members
    Registry = ReadRegistry(Payload, 0, len(Payload))
    assert len(Registry.References) == 2
    assert Registry.References[0].Name == "UGS::OM::Meta"
    assert Registry.References[1].Code == 0x30
    assert len(Registry.Classes) == 2
    assert Registry.Classes[0].Name == "UGS::OM::RootObject"
    assert Registry.Classes[0].Storage == 56
    assert Registry.Classes[0].Fingerprint == bytes.fromhex("b04ba5fe911bf679")
    assert Registry.Classes[0].Reference == 2
    assert Registry.Classes[1].Name == "UGS::RM_part"
    assert Registry.Classes[1].Storage == 101
    assert len(Registry.Members) == 1
    assert Registry.Members[0].Name == "first_record_area"
    assert Registry.Members[0].Owner == 28
    assert WriteRegistry(Registry) == Payload


# the registry writer reproduces the vendor token widths and the separator byte
def TestNxTypeWrite() -> None:
    assert WriteToken(5001) == bytes([0xA0, 0x13, 0x88])
    assert WriteToken(71001) == bytes([0xA1, 0x15, 0x58])
    assert WriteToken(None) == bytes([0xFF])
    assert WriteToken(56) == bytes([56])
    assert WriteToken(1001) == bytes([0x83, 0xE8])
