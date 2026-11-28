from pathlib import Path as FilePath
from struct import pack as PackValues

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.DesignTextures.CheckMapGraph import CheckMapGraph


# the persisted json and design owners must retain the exact initialized placement
def ReadTexture(Source: FilePath, Origin: tuple[float, float, float]) -> CadDocument:
    Model = ReadDocument(Source.read_bytes())
    CheckMapGraph(Model, Origin)
    assert Model.Graphics is None
    Document = OpenDocument(Source)
    Durable = CadDocument.from_json(Document.to_json())
    assert Durable == Document and Durable.metadata["fusion.read_only"] is True
    State = CheckContract(Durable.metadata["fusion.native_state"], "model", Version=2)
    assert isinstance(State, DocumentModel) and State == Model
    StateGraph = BuildGraph(State)
    StateWood = StateGraph.OneClass("ProceduralWoodTextureMapping")
    assert PackValues(">ddd", *PointCoords(StateWood.Fields["origin"])) == PackValues(
        ">ddd", *Origin
    )
    return Durable
