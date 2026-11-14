from __future__ import annotations

from dataclasses import replace as Replace
from io import BytesIO as BytesIo
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.creo.Adapter import CreoAdapter
from convert.adapters.creo.CreoFormat import CreoFormat
from convert.adapters.creo.Format import KFormatId
from interchange.enums.EnumUnits import UnitSystem


def TocRow(
    NameText: str,
    Offset: int,
    Length: int,
    Expanded: int,
) -> bytes:
    RowText = f"{NameText} {Offset:x} {Length:x} {Expanded:x} 1934 9 -1 0000 0000"
    return RowText.encode("ascii").ljust(80, b"#")[:80] + b"\n"


def BuildSample(KindText: str = "PART", Damaged: bool = False) -> bytes:
    FirstLine = f"#UGC:2 {KindText} 1 2 3 4 5 6 7 8 00000000 \\".encode("ascii")
    HeaderBody = b"\n#- CMNM 008Test.prt\n#-END_OF_UGC_HEADER\n"
    Header = FirstLine + HeaderBody
    BaseValue = len(Header)
    Header = Header.replace(b"00000000", f"{BaseValue:08x}".encode("ascii"), 1)
    Banner = b"#Creo  TM  Version 13.0 (c) 2026 by PTC Inc.\n"
    TocHead = b"#UGC_TOC 2 2 81 17".ljust(80, b"#")[:80] + b"\n"
    Geometry = b"#VisibGeom\n\xe0\x00root\x00\xe3"
    Thumb = b"#THMB_IMG_MAIN\n\xff\xd8\xff\xd9"
    BodyStart = BaseValue + len(Banner) + len(TocHead) + 162
    GeometryLength = len(Geometry) + (1000 if Damaged else 0)
    RowList = TocRow("VisibGeom", BodyStart - BaseValue, GeometryLength, 6) + TocRow(
        "THMB_IMG_MAIN",
        BodyStart - BaseValue + len(Geometry),
        len(Thumb),
        4,
    )
    return Header + Banner + TocHead + RowList + Geometry + Thumb


def TestRead() -> None:
    AdapterValue = CreoAdapter()
    DataValue = BuildSample()
    ProbeValue = AdapterValue.probe(DataValue)
    assert ProbeValue.format_id == KFormatId
    assert ProbeValue.confidence == 1.0
    DocumentValue = AdapterValue.read(DataValue)
    assert DocumentValue.source.format_id == KFormatId
    assert DocumentValue.source.container_version == "PSB"
    assert DocumentValue.source.application_version == "13.0"
    assert DocumentValue.metadata["creo.kind"] == "PART"
    assert DocumentValue.metadata["creo.common_name"] == "Test.prt"
    assert DocumentValue.metadata["creo.section_count"] == 2
    assert DocumentValue.metadata["creo.section_names"] == (
        "VisibGeom",
        "THMB_IMG_MAIN",
    )
    assert DocumentValue.metadata["creo.thumbnail_present"] is True
    assert len(DocumentValue.brep_payloads) == 1
    assert DocumentValue.brep_payloads[0].data == b"\xff\xd8\xff\xd9"
    assert DocumentValue.feature_timeline == ()
    assert DocumentValue.bodies == ()


def TestReplay() -> None:
    AdapterValue = CreoAdapter()
    DataValue = BuildSample()
    DocumentValue = AdapterValue.read(DataValue)
    with TemporaryDirectory() as Folder:
        Target = FilePath(Folder) / "copy.prt"
        ResultValue = AdapterValue.write(DocumentValue, Target)
        assert Target.read_bytes() == DataValue
        assert ResultValue.bytes_written == len(DataValue)
        assert ResultValue.application_usable is False
        assert ResultValue.vendor_loadable is False
        assert ResultValue.metadata["mode"] == "exact_native_roundtrip"


def TestPublic() -> None:
    DataValue = BuildSample()
    DocumentValue = OpenDoc(DataValue, source_format=KFormatId)
    with TemporaryDirectory() as Folder:
        Target = FilePath(Folder) / "copy.prt"
        ResultValue = WriteDoc(DocumentValue, Target, destination_format=KFormatId)
        assert Target.read_bytes() == DataValue
        assert ResultValue.bytes_written == len(DataValue)


def TestEdited() -> None:
    AdapterValue = CreoAdapter()
    DocumentValue = AdapterValue.read(BuildSample())
    EditedValue = Replace(DocumentValue, units=UnitSystem.KInch)
    with TemporaryDirectory() as Folder:
        Target = FilePath(Folder) / "copy.prt"
        try:
            _ = AdapterValue.write(EditedValue, Target)
        except CreoFormat as ErrorInfo:
            assert "edited" in str(ErrorInfo)
        else:
            raise AssertionError("edited Creo document must not replay")


def TestAssembly() -> None:
    AdapterValue = CreoAdapter()
    ProbeValue = AdapterValue.probe(BuildSample("ASSEMBLY"))
    assert ProbeValue.confidence == 0.0
    try:
        _ = AdapterValue.read(BuildSample("ASSEMBLY"))
    except CreoFormat as ErrorInfo:
        assert "assembly" in str(ErrorInfo).casefold()
    else:
        raise AssertionError("assembly must not read as a part")


def TestConfig() -> None:
    AdapterValue = CreoAdapter()
    try:
        _ = AdapterValue.read(
            BuildSample(), Options=ReadOptions(configuration="production")
        )
    except CreoFormat as ErrorInfo:
        assert "configuration" in str(ErrorInfo).casefold()
    else:
        raise AssertionError("unknown configuration must be rejected")


def TestDamaged() -> None:
    AdapterValue = CreoAdapter()
    ProbeValue = AdapterValue.probe(BuildSample(Damaged=True))
    assert ProbeValue.confidence == 0.0
    try:
        _ = AdapterValue.read(BuildSample(Damaged=True))
    except CreoFormat:
        pass
    else:
        raise AssertionError("damaged table of contents must be rejected")


def TestStream() -> None:
    AdapterValue = CreoAdapter()
    StreamValue = BytesIo(BuildSample())
    _ = AdapterValue.probe(StreamValue)
    assert StreamValue.tell() == 0


def TestBadInput() -> None:
    AdapterValue = CreoAdapter()
    ProbeValue = AdapterValue.probe(b"#UGC:2 PART 1")
    assert ProbeValue.confidence == 0.0
