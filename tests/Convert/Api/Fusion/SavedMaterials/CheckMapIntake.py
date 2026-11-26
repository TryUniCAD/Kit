from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedMaterials.GenMappedBody import GenMappedBody


# scoped material preparation must refuse a mapping that public json still preserves exactly
def CheckMapIntake(Candidate: FilePath, ResearchFolder: str, PrefixValue: str) -> None:
    Payload = GenMappedBody(Candidate.read_bytes())
    Native = ReadDocument(Payload)
    Graph = BuildGraph(Native)
    BodyNode = SelectExtrusion(Graph).BodyNode
    Mapped = ResolveField(Graph, BodyNode, "textureMapping", "LayeredTextureMapping")
    assert Mapped.Fields["activeLayer"] == 0 and Native.Graphics is None
    Source = Candidate.with_name("Mapped.f3d")
    _ = Source.write_bytes(Payload)
    Document = OpenDocument(Source)
    Loaded = CadDocument.from_json(Document.to_json())
    assert Loaded.metadata["fusion.read_only"] is True
    assert (
        CheckContract(Loaded.metadata["fusion.native_state"], "model", Version=2)
        == Native
    )
    Request = Source.with_name("Mapped.json")
    Project = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder=ResearchFolder
    )
    assert Project.returncode == 1 and not Request.exists()
    assert (
        Project.stderr.strip()
        == f"{PrefixValue}: Saved Design texture mapping is unsupported"
    )
    assert Source.read_bytes() == Payload
