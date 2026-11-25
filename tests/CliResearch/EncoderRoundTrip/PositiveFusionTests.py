from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import approx as NearValue, mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.Features.FeatureDistExt import DistanceExtrude
from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# fresh authored native inputs must exercise candidate generation and preserve explicit driving geometry through the installed command
@TestMark.parametrize("EditedHeight", (14.2, 9.6))
def CheckFusionFlow(TmpPath: FilePath, EditedHeight: float) -> None:
    WidthMm, DepthMm, HeightMm = 23.4, 17.8, 9.6
    SourceDoc = MakeFusionDoc(
        DocumentSpec(
            "Fresh Encoder Cuboid",
            "kitHeight",
            HeightMm,
            ProfileKind="cuboid",
            SketchName="Encoder Rectangle",
            ExtrusionName="Encoder Extrusion",
            BodyName="Encoder Cuboid",
            WidthMm=WidthMm,
            DepthMm=DepthMm,
            ConstrainRectangle=True,
            WidthParamName="kitWidth",
            DepthParamName="kitDepth",
        )
    )
    SourcePath, OutputPath = TmpPath / "Source.f3d", TmpPath / "RoundTrip"
    SourceResult = WriteDocument(
        SourceDoc, SourcePath, DestFormat="fusion.f3d", AllowCarrier=False
    )
    assert not SourceResult.dropped and not SourceResult.carrier_capabilities
    SourceBytes = SourcePath.read_bytes()
    Result = RunEncoder(
        TmpPath,
        "fusion",
        SourcePath,
        OutputPath,
        str(EditedHeight),
        LocatorValue=r"C:\KitEncoderRoundTrip",
    )
    IsNoop = EditedHeight == HeightMm
    assert Result.returncode == (3 if IsNoop else 0), Result.stderr
    Manifest = DecodeJson((OutputPath / "manifest.json").read_bytes())
    assert Manifest["status"] == ("incomplete" if IsNoop else "awaiting_native")
    assert Manifest["source"]["status"] == "decoded"
    assert Manifest["source_sha256"] == HashContent(SourceBytes).hexdigest()
    assert Manifest["models_used"] is False
    assert Manifest["vendor_loadable"] is False
    assert Manifest["application_usable"] is False
    Cases: tuple[tuple[str, float], ...] = (("reconstruction", HeightMm),)
    if IsNoop:
        assert Manifest["edited"]["status"] == "unsupported"
        assert "must change the driving value" in Manifest["edited"]["reason"]
        assert not (OutputPath / "edited.f3d").exists()
    else:
        Cases += (("edited", EditedHeight),)
    for RoleName, ExpectedHeight in Cases:
        assert Manifest[RoleName]["status"] == "awaiting_native"
        NativePath = OutputPath / (RoleName + ".f3d")
        assert (
            HashContent(NativePath.read_bytes()).hexdigest()
            == Manifest["candidate_sha256"][RoleName]
        )
        Document = OpenDocument(NativePath, SourceFormat="fusion.f3d", StrictMode=True)
        assert not Document.diagnostics and not Document.brep_payloads
        assert len(Document.feature_timeline) == 2
        Definition = Document.feature_timeline[-1].definition
        assert isinstance(Definition, DistanceExtrude)
        Parameters = {Parameter.id: Parameter for Parameter in Document.parameters}
        Distance = Parameters[Definition.AlongParameterId]
        assert Distance.value.unit == "mm"
        assert Distance.value.value == NearValue(ExpectedHeight)
        assert Distance.expression is not None
        assert len(Distance.expression.parameter_ids) == 1
        Driver = Parameters[Distance.expression.parameter_ids[0]]
        assert Driver.name == "kitHeight"
        assert Driver.value.value == NearValue(ExpectedHeight)
        assert len(Document.bodies) == 1 and Document.brep is not None
        Topology = Document.bodies[0].topology
        assert (
            Topology.solid_count,
            Topology.face_count,
            Topology.edge_count,
            Topology.vertex_count,
        ) == (1, 6, 12, 8)
        assert Topology.volume == NearValue(
            WidthMm * DepthMm * ExpectedHeight, rel=1e-10, abs=1e-8
        )
        Corners = sorted(
            (XCoord, YCoord, ZCoord)
            for XCoord in (0.0, WidthMm)
            for YCoord in (0.0, DepthMm)
            for ZCoord in (0.0, ExpectedHeight)
        )
        Vertices = sorted(
            (Vertex.point.x, Vertex.point.y, Vertex.point.z)
            for Vertex in Document.brep.vertices
        )
        for Observed, Expected in zip(Vertices, Corners, strict=True):
            assert Observed == NearValue(Expected, rel=1e-10, abs=1e-8)
    assert SourcePath.read_bytes() == SourceBytes
    if IsNoop:
        Snapshot = {
            Entry.name: HashContent(Entry.read_bytes()).hexdigest()
            for Entry in OutputPath.iterdir()
        }
        Retried = RunEncoder(
            TmpPath, "fusion", SourcePath, OutputPath, str(EditedHeight)
        )
        assert Retried.returncode == 1, Retried.stderr
        assert Snapshot == {
            Entry.name: HashContent(Entry.read_bytes()).hexdigest()
            for Entry in OutputPath.iterdir()
        }
