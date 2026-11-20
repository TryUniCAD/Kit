from hashlib import sha256 as Fingerprint
from math import hypot as Hypot, isclose as IsClose

from convert import open_document as OpenDocument
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepLoop
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
    assert ModelValue is not None and not ModelValue.validate()
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


# the active partition alone cannot qualify the local body when history is absent
def TestNoHistory() -> None:
    Archive = SldprtArchive.from_bytes(ReadFixture("RectangularBare", KRectangle))
    Streams = Archive.streams
    ActiveValue, HistoryValue = DecodePartition(
        Streams[KPartitionStream], KPartitionStream
    )
    assert (ActiveValue.kind, HistoryValue.kind) == ("partition", "deltas")
    Streams[KPartitionStream] = ActiveValue.data
    Document = OpenDocument(
        BuildSldprt(
            Streams, FileId=Archive.file_id, FormatVersion=Archive.format_version
        ),
        source_format="solidworks.sldprt",
        strict=True,
        include_brep=True,
        include_tessellation=False,
    )
    assert len(Document.brep_payloads) == 2
    assert {
        (Payload.source_stream, Payload.kind) for Payload in Document.brep_payloads
    } == {
        (KLocalBodyStream, "unknown"),
        (KPartitionStream, "partition"),
    }
    assert Document.brep is None


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
