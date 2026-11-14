from __future__ import annotations

from pathlib import Path as FilePath
from tempfile import TemporaryDirectory

from convert.adapters.creo.Adapter import CreoAdapter
from convert.adapters.creo.Format import KFormatId


def TocRow(
    NameText: str,
    Offset: int,
    Length: int,
    Expanded: int,
) -> bytes:
    RowText = f"{NameText} {Offset:x} {Length:x} {Expanded:x} 1934 9 -1 0000 0000"
    return RowText.encode("ascii").ljust(80, b"#")[:80] + b"\n"


def BuildSample() -> bytes:
    FirstLine = b"#UGC:2 PART 1 2 3 4 5 6 7 8 00000000 \\"
    HeaderBody = b"\n#- CMNM 008Test.prt\n#-END_OF_UGC_HEADER\n"
    Header = FirstLine + HeaderBody
    BaseValue = len(Header)
    Header = Header.replace(b"00000000", f"{BaseValue:08x}".encode("ascii"), 1)
    Banner = b"#Creo  TM  Version 13.0 (c) 2026 by PTC Inc.\n"
    TocHead = b"#UGC_TOC 2 2 81 17".ljust(80, b"#")[:80] + b"\n"
    Geometry = b"#VisibGeom\n\xe0\x00root\x00\xe3"
    Thumb = b"#THMB_IMG_MAIN\n\xff\xd8\xff\xd9"
    BodyStart = BaseValue + len(Banner) + len(TocHead) + 162
    Rows = TocRow("VisibGeom", BodyStart - BaseValue, len(Geometry), 6) + TocRow(
        "THMB_IMG_MAIN",
        BodyStart - BaseValue + len(Geometry),
        len(Thumb),
        4,
    )
    return Header + Banner + TocHead + Rows + Geometry + Thumb


def TestContainerRead() -> None:
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


def TestSourceReplay() -> None:
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


def TestDamagedInput() -> None:
    AdapterValue = CreoAdapter()
    ProbeValue = AdapterValue.probe(b"#UGC:2 PART 1")
    assert ProbeValue.confidence == 0.0
