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


def BuildFeatureSample() -> bytes:
    FirstLine = f"#UGC:2 PART 1 2 3 4 5 6 7 8 00000000 \\".encode("ascii")
    HeaderBody = b"\n#- CMNM 008Test.prt\n#-END_OF_UGC_HEADER\n"
    Header = FirstLine + HeaderBody
    BaseValue = len(Header)
    Header = Header.replace(b"00000000", f"{BaseValue:08x}".encode("ascii"), 1)
    Banner = b"#Creo  TM  Version 13.0 (c) 2026 by PTC Inc.\n"
    TocHead = b"#UGC_TOC 2 4 81 17".ljust(80, b"#")[:80] + b"\n"
    FeatureBody = (
        b"\xe3\x07\x00\x00\xe3\xf6\x83\x9b\xe1"
        + b"\x00" * 8
        + b"\xe3\x05\x00\x00\xe3\xf6\x83\x95\xe1"
        + b"\x00" * 8
    )
    Feature = b"#AllFeatur\n" + FeatureBody
    DefinitionBody = (
        b"\xe0\x02value\x00"
        + b"\x2d\x69\x37\x02\xbe\xe2\x92\x0c"
        + b"\xe0\x01dim_ref\x00\x07"
    )
    Definition = b"#FeatDefs\n" + DefinitionBody
    GeometryBody = (
        b"\xe0\x00srf_array\x00\xf8\x01\xf7\x03\xfb\xe3"
        + b"\xe0\x01geom_id\x00\x4d"
        + b"\xe0\x01geom_type\x00\x22"
        + b"\xe0\x01feat_id\x00\x4a"
        + b"\xe0\x02envlp\x00\xf9\x02\x02\x18\xe7\x03"
        + b"\xe0\x02outline\x00\xf9\x02\x03\x18\xe7\x05"
    )
    Geometry = b"#VisibGeom\n" + GeometryBody
    Thumb = b"#THMB_IMG_MAIN\n\xff\xd8\xff\xd9"
    BodyStart = BaseValue + len(Banner) + len(TocHead) + 324
    RowList = (
        TocRow("AllFeatur", BodyStart - BaseValue, len(Feature), len(FeatureBody))
        + TocRow(
            "FeatDefs",
            BodyStart - BaseValue + len(Feature),
            len(Definition),
            len(DefinitionBody),
        )
        + TocRow(
            "VisibGeom",
            BodyStart - BaseValue + len(Feature) + len(Definition),
            len(Geometry),
            len(GeometryBody),
        )
        + TocRow(
            "THMB_IMG_MAIN",
            BodyStart - BaseValue + len(Feature) + len(Definition) + len(Geometry),
            len(Thumb),
            4,
        )
    )
    return (
        Header
        + Banner
        + TocHead
        + RowList
        + Feature
        + Definition
        + Geometry
        + Thumb
    )


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


def TestFeatureRows() -> None:
    AdapterValue = CreoAdapter()
    DocumentValue = AdapterValue.read(BuildFeatureSample())
    FeatureIds = tuple(
        FeatureValue.id for FeatureValue in DocumentValue.feature_timeline
    )
    assert FeatureIds == ("creo:feature:7", "creo:feature:5")
    assert tuple(
        FeatureValue.order for FeatureValue in DocumentValue.feature_timeline
    ) == (0, 1)
    FirstValue = DocumentValue.feature_timeline[0]
    assert FirstValue.name == "Creo datum_plane 7"
    assert FirstValue.attributes["creo.feature_id"] == 7
    assert FirstValue.attributes["creo.root_class"] == 923
    assert FirstValue.attributes["creo.root_class_label"] == "datum_plane"
    assert FirstValue.provenance is not None
    assert FirstValue.provenance.spans[0].stream == "AllFeatur"
    SecondValue = DocumentValue.feature_timeline[1]
    assert SecondValue.name == "Creo protrusion 5"
    assert SecondValue.parameter_ids == ("creo:dimension:0",)
    assert len(DocumentValue.parameters) == 1
    ParameterValue = DocumentValue.parameters[0]
    assert ParameterValue.id == "creo:dimension:0"
    assert ParameterValue.name == "Creo dimension 0"
    assert ParameterValue.value.value == -201.7190851617055
    assert ParameterValue.owner_id == "creo:feature:5"
    assert ParameterValue.provenance is not None
    assert ParameterValue.provenance.spans[0].stream == "FeatDefs"
    assert DocumentValue.metadata["creo.feature_rows_decoded"] is True
    assert DocumentValue.metadata["creo.feature_row_count"] == 2
    assert DocumentValue.metadata["creo.dimension_count"] == 1
    assert DocumentValue.metadata["creo.parameters_decoded"] is True
    assert DocumentValue.metadata["creo.surface_count"] == 1
    assert DocumentValue.metadata["creo.curve_count"] == 0
    assert DocumentValue.metadata["creo.surface_prototypes_decoded"] is True
    assert len(DocumentValue.bodies) == 1
    BodyValue = DocumentValue.bodies[0]
    assert BodyValue.id == "creo:body:1"
    assert BodyValue.final_feature_id == "creo:feature:5"
    assert BodyValue.topology.face_count == 1
    assert BodyValue.topology.edge_count == 0
    assert BodyValue.topology.solid_count == 0
    assert BodyValue.topology.shell_count == 0
    assert BodyValue.topology.valid is False
    assert BodyValue.topology.volume is None
    assert BodyValue.topology.vertex_count == 0
    assert DocumentValue.metadata["creo.shell_closure_proven"] is False
    assert DocumentValue.metadata["creo.volume"] is None
    assert DocumentValue.metadata["creo.centroid"] is None
    Faces = BodyValue.attributes["creo.faces"]
    assert tuple(Face["id"] for Face in Faces) == ("creo:face:77",)
    assert Faces[0]["geom_type"] == 34
    assert Faces[0]["feature_id"] == 74
    assert Faces[0]["envelope"] == (1.0, 1.0, 1.0, 1.0)
    assert BodyValue.attributes["creo.logical_objects"] == ()
    assert DocumentValue.metadata["creo.logical_object_count"] == 0
    assert DocumentValue.metadata["creo.feature_history_decoded"] is False
    assert DocumentValue.metadata["creo.geometry_decoded"] is False


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
