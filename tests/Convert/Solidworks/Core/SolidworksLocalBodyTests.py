from hashlib import sha256 as Fingerprint
from math import hypot as Hypot, isclose as IsClose
from struct import pack as PackValue
from tempfile import TemporaryDirectory

from convert import extract_brep as ExtractPayloads
from convert import open_document as OpenDocument
from convert.Geometry.Parasolid import EncodePartData, ParaHeaderData
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadRollbackMut import (
    ReadRollbackMut,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Container.Container import (
    BuildSldprt,
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Native import ReadSerialized
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepLoop
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Api.ApiTestPaths import KRootPath

# both positive containers are the exact disclosed inputs to the native probe
KLocalParts = KRootPath / "re/solidworks/v2026/corpus/local-import-readback"

# the rectangular hash binds the metadata and missing history controls
KRectangle = "302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357"


# fixture bytes must match the native receipt before entering the public reader
def ReadFixture(CaseName: str, CaseDigest: str) -> bytes:
    DataValue = (KLocalParts / f"{CaseName}.SLDPRT").read_bytes()
    assert Fingerprint(DataValue).hexdigest() == CaseDigest
    return DataValue


# directed coedges determine the actual winding of each trimmed face
def RingPoints(ModelValue: BrepModel, LoopValue: BrepLoop) -> tuple[SpaceVector, ...]:
    Vertices = {Vertex.id: Vertex.point for Vertex in ModelValue.vertices}
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in ModelValue.edges}
    UseById = {UseValue.id: UseValue for UseValue in ModelValue.coedges}
    Endpoints: list[tuple[str, str]] = []
    for UseId in LoopValue.coedge_ids:
        UseValue = UseById[UseId]
        EdgeValue = Edges[UseValue.edge_id]
        FirstId, FinalId = EdgeValue.start_vertex_id, EdgeValue.end_vertex_id
        Endpoints.append(
            (FinalId, FirstId) if UseValue.reversed else (FirstId, FinalId)
        )
    assert all(
        FinalId == NextId
        for (_, FinalId), (NextId, _) in zip(Endpoints, Endpoints[1:] + Endpoints[:1])
    )
    return tuple(Vertices[FirstId] for FirstId, _ in Endpoints)


# signed triangle contributions preserve concave area and outward volume
def RingMeasures(
    Points: tuple[SpaceVector, ...],
) -> tuple[float, float, SpaceVector]:
    Crosses = tuple(
        CrossVector(First, Second)
        for First, Second in zip(Points, Points[1:] + Points[:1])
    )
    AreaValue = (
        Hypot(
            sum(Vector.x for Vector in Crosses),
            sum(Vector.y for Vector in Crosses),
            sum(Vector.z for Vector in Crosses),
        )
        / 2
    )
    First = Points[0]
    Volume = 0.0
    XMoment = YMoment = ZMoment = 0.0
    for Second, Third in zip(Points[1:], Points[2:]):
        SixVolume = DotVector(First, CrossVector(Second, Third))
        Volume += SixVolume
        XMoment += SixVolume * (First.x + Second.x + Third.x)
        YMoment += SixVolume * (First.y + Second.y + Third.y)
        ZMoment += SixVolume * (First.z + Second.z + Third.z)
    return Volume, AreaValue, SpaceVector(XMoment, YMoment, ZMoment)


# native mass observations require a measurement separate from topology construction
def ShellMeasures(
    ModelValue: BrepModel,
) -> tuple[float, float, tuple[float, float, float]]:
    Measures = tuple(
        RingMeasures(RingPoints(ModelValue, LoopValue))
        for LoopValue in ModelValue.loops
    )
    SixVolume = sum(Volume for Volume, _, _ in Measures)
    assert SixVolume > 0
    Divisor = 4 * SixVolume
    Centroid = (
        sum(Moment.x for _, _, Moment in Measures) / Divisor,
        sum(Moment.y for _, _, Moment in Measures) / Divisor,
        sum(Moment.z for _, _, Moment in Measures) / Divisor,
    )
    return SixVolume / 6, sum(AreaValue for _, AreaValue, _ in Measures), Centroid


# public import ownership must agree with both the native feature and solid summary
def AssertBodyOwner(
    Document: CadDocument, ModelValue: BrepModel, Counts: tuple[int, int, int]
) -> None:
    (OwnerValue,) = (
        StepValue
        for StepValue in Document.feature_timeline
        if StepValue.kind == FeatureKind.IMPORTED
    )
    assert OwnerValue.name == "Imported geometry"
    assert OwnerValue.attributes["native_type"] == "Imported"
    assert OwnerValue.attributes["xml_tag"] == "Feature"
    assert OwnerValue.attributes["native_object_id"] == 18
    assert OwnerValue.operation is None and not OwnerValue.parameter_ids
    (BodyValue,) = Document.bodies
    assert BodyValue.final_feature_id == OwnerValue.id
    assert BodyValue.attributes["native_object_id"] == 18
    assert (
        BodyValue.provenance is not None
        and BodyValue.provenance == OwnerValue.provenance
    )
    assert ModelValue.bodies[0].design_body_id == BodyValue.id
    Summary = BodyValue.topology
    assert (Summary.solid_count, Summary.shell_count) == (1, 1)
    assert (Summary.face_count, Summary.edge_count, Summary.vertex_count) == Counts


# strict public reads qualify the measured topology and payload group together
def AssertLocalRead(
    CaseName: str,
    CaseDigest: str,
    Counts: tuple[int, int, int],
    Volume: float,
    AreaValue: float,
    Centroid: tuple[float, float, float],
) -> None:
    Document = OpenDocument(
        ReadFixture(CaseName, CaseDigest),
        source_format="solidworks.sldprt",
        strict=True,
        include_brep=True,
        include_tessellation=False,
    )
    assert len(Document.brep_payloads) == 3
    assert {
        (Payload.source_stream, Payload.kind) for Payload in Document.brep_payloads
    } == {
        (KLocalBodyStream, "unknown"),
        (KPartitionStream, "partition"),
        (KPartitionStream, "deltas"),
    }
    ModelValue = Document.brep
    assert ModelValue is not None
    assert not ModelValue.validate(
        frozenset(BodyValue.id for BodyValue in Document.bodies)
    )
    assert len(ModelValue.bodies) == 1
    (ShellValue,) = ModelValue.shells
    assert ShellValue.closed
    (RegionValue,) = ModelValue.regions
    assert RegionValue.solid
    assert (
        len(ModelValue.faces),
        len(ModelValue.edges),
        len(ModelValue.vertices),
    ) == Counts
    AssertBodyOwner(Document, ModelValue, Counts)
    ActualVolume, ActualArea, ActualCenter = ShellMeasures(ModelValue)
    assert IsClose(ActualVolume, Volume, rel_tol=2e-7)
    assert IsClose(ActualArea, AreaValue, rel_tol=2e-7)
    assert all(
        IsClose(Actual, Expected, rel_tol=2e-7)
        for Actual, Expected in zip(ActualCenter, Centroid)
    )


# the bare rectangle checks the smallest measured local solid
def TestLocalRect() -> None:
    AssertLocalRead(
        "RectangularBare", KRectangle, (6, 12, 8), 2574.0, 1150.0, (-2.5, 14.0, 8.5)
    )


# the attributed concave solid checks a variable boundary and body metadata
def TestLocalPrism() -> None:
    AssertLocalRead(
        "ConcaveOwned",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        (8, 18, 12),
        5160.0,
        2068.0,
        (17.44186046511628, -4.30232558139535, 3.5),
    )


# all probe phases read the controlled archive through the public sdk
def ReadLocalProbe(
    DataValue: bytes, *, Strict: bool, IncludeBrep: bool = True
) -> CadDocument:
    return OpenDocument(
        DataValue,
        source_format="solidworks.sldprt",
        strict=Strict,
        include_brep=IncludeBrep,
        include_tessellation=False,
    )


# each probe must publish its controlled streams into the same native container format
def BuildLocalProbe(Archive: SldprtArchive, Streams: dict[str, bytes]) -> bytes:
    return BuildSldprt(
        Streams, FileId=Archive.file_id, FormatVersion=Archive.format_version
    )


# strict reads reject loss and partial reads retain the source with a warning
def AssertLocalStop(DataValue: bytes, Reason: str) -> CadDocument:
    try:
        _ = ReadLocalProbe(DataValue, Strict=True)
    except SldprtFormatError as ErrorInfo:
        assert "SLDPRT local geometry rejected" in str(ErrorInfo)
        assert Reason in str(ErrorInfo)
    else:
        raise AssertionError("strict read accepted a rejected local solid")
    Partial = ReadLocalProbe(DataValue, Strict=False)
    assert Partial.brep is None
    (Diagnostic,) = (
        Entry
        for Entry in Partial.diagnostics
        if Entry.code == "sldprt.local_geometry_rejected"
    )
    assert Diagnostic.severity == Severity.WARNING
    assert Diagnostic.attributes["stream"] == KLocalBodyStream
    assert Reason in Diagnostic.message
    Metadata = ReadLocalProbe(DataValue, Strict=True, IncludeBrep=False)
    assert Metadata.brep is None and not Metadata.brep_payloads
    return Partial


# the active partition alone cannot qualify the local body when history is absent
def TestNoHistory() -> None:
    Archive = SldprtArchive.from_bytes(ReadFixture("RectangularBare", KRectangle))
    Streams = Archive.streams
    ActiveValue, HistoryValue = DecodePartition(
        Streams[KPartitionStream], KPartitionStream
    )
    assert (ActiveValue.kind, HistoryValue.kind) == ("partition", "deltas")
    Streams[KPartitionStream] = ActiveValue.data
    DataValue = BuildLocalProbe(Archive, Streams)
    Document = AssertLocalStop(DataValue, "rollback history is missing")
    assert len(Document.brep_payloads) == 2
    assert {
        (Payload.source_stream, Payload.kind) for Payload in Document.brep_payloads
    } == {
        (KLocalBodyStream, "unknown"),
        (KPartitionStream, "partition"),
    }
    with TemporaryDirectory() as Target:
        Paths = ExtractPayloads(DataValue, Target, source_format="solidworks.sldprt")
        assert len(Paths) == 2
        assert {Fingerprint(Entry.read_bytes()).hexdigest() for Entry in Paths} == {
            Payload.sha256 for Payload in Document.brep_payloads
        }


# raw extraction still rejects a truncated native compression frame
def TestRawFraming() -> None:
    Archive = SldprtArchive.from_bytes(ReadFixture("RectangularBare", KRectangle))
    Streams = Archive.streams
    ActiveValue, _ = DecodePartition(Streams[KPartitionStream], KPartitionStream)
    Streams[KPartitionStream] = EncodePartData(ActiveValue.data)[:-1]
    DataValue = BuildLocalProbe(Archive, Streams)
    with TemporaryDirectory() as Target:
        try:
            _ = ExtractPayloads(DataValue, Target, source_format="solidworks.sldprt")
        except SldprtFormatError as ErrorInfo:
            assert "truncated Parasolid chain section" in str(ErrorInfo)
        else:
            raise AssertionError("raw extraction accepted a truncated Parasolid frame")


# a retained history may select an earlier real mark in the same native chain
def RetargetHistory(ActiveData: bytes, HistoryData: bytes) -> bytes:
    ActiveNodes = ReadActiveNodes(ActiveData)
    HeaderValue = ParaHeaderData(HistoryData)
    assert HeaderValue is not None
    Cursor = XmtCursor(HistoryData[HeaderValue.body_offset :])
    assert Cursor.ReadKind() == 3
    RootShape = KKernelShapes[3]
    Cursor.ExpectBytes(SchemaHeader(RootShape))
    PartitionId = Cursor.ReadIndex()
    assert PartitionId and PartitionId not in ActiveNodes
    MarkStart = HeaderValue.body_offset + Cursor.OffsetValue
    SelectedIndex = Cursor.ReadIndex()
    MarkEnd = HeaderValue.body_offset + Cursor.OffsetValue
    assert MarkEnd - MarkStart == 2
    MarkField, HighestField = RootShape.FieldsValue
    assert MarkField.NameValue == "current_pmark"
    assert HighestField.NameValue == "highest_id"
    assert ReadXmtValueMut(Cursor, HighestField) == ActiveNodes[1].Integer("highest_id")
    MarkIndices: dict[int, int] = {}
    while (KindValue := Cursor.ReadKind()) != 1:
        assert KindValue == 4
        MarkValue = ReadXmtNodeMut(Cursor, KindValue)
        MarkIndices[MarkValue.Integer("id")] = MarkValue.IndexValue
        if MarkValue.Integer("delta_key"):
            _ = ReadRollbackMut(Cursor, ActiveNodes)
    Cursor.FinishRead()
    assert MarkIndices[ActiveNodes[1].Integer("current_id")] == SelectedIndex
    assert SelectedIndex != MarkIndices[1] and MarkIndices[1] < 32767
    return (
        HistoryData[:MarkStart]
        + PackValue(">H", MarkIndices[1] + 1)
        + HistoryData[MarkEnd:]
    )


# a realistic retained rollback cannot qualify an inconsistent active world
def TestWrongMarks() -> None:
    Archive = SldprtArchive.from_bytes(ReadFixture("RectangularBare", KRectangle))
    Streams = Archive.streams
    ActiveValue, HistoryValue = DecodePartition(
        Streams[KPartitionStream], KPartitionStream
    )
    HistoryData = RetargetHistory(ActiveValue.data, HistoryValue.data)
    Streams[KPartitionStream] = EncodePartData(ActiveValue.data) + EncodePartData(
        HistoryData
    )
    Document = AssertLocalStop(
        BuildLocalProbe(Archive, Streams), "world and history identities disagree"
    )
    assert {Payload.kind: Payload.sha256 for Payload in Document.brep_payloads} == {
        "unknown": next(
            Payload.sha256
            for Payload in DecodePartition(Streams[KLocalBodyStream], KLocalBodyStream)
        ),
        "partition": ActiveValue.sha256,
        "deltas": Fingerprint(HistoryData).hexdigest(),
    }
    assert len(Document.brep_payloads) == 3


# a complete local group with a different key must not attach to the import
def TestWrongOwner() -> None:
    Archive = SldprtArchive.from_bytes(ReadFixture("RectangularBare", KRectangle))
    Streams = Archive.streams
    GroupData = Streams[KLocalBodyStream]
    OwnerName, NameEnd = ReadSerialized(GroupData, 4)
    assert OwnerName == "Imported geometry"
    StemBytes = OwnerName.swapcase().encode("utf-16le")
    NameStart = NameEnd - len(StemBytes)
    Streams[KLocalBodyStream] = GroupData[:NameStart] + StemBytes + GroupData[NameEnd:]
    Document = AssertLocalStop(
        BuildLocalProbe(Archive, Streams),
        "storage key differs from its resolved import",
    )
    assert len(Document.brep_payloads) == 3


# metadata reads keep the geometry intake and payload materialization disabled
def TestNoLocalBrep() -> None:
    Document = OpenDocument(
        ReadFixture("RectangularBare", KRectangle),
        source_format="solidworks.sldprt",
        strict=True,
        include_brep=False,
        include_tessellation=False,
    )
    assert Document.brep is None and not Document.brep_payloads
