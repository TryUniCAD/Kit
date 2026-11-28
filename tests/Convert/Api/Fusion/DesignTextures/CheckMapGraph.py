from struct import pack as PackValues
from sys import float_info as FloatLimits

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# verify the generated mapping classes ownership and exact empty cache representation
def CheckMapGraph(
    ModelValue: DocumentModel, Origin: tuple[float, float, float]
) -> None:
    Graph = BuildGraph(ModelValue)
    BodyNode = SelectExtrusion(Graph).BodyNode
    Layered = ResolveField(Graph, BodyNode, "textureMapping", "LayeredTextureMapping")
    assert isinstance(BodyNode.Fields["textureMapping"], LocalRef)
    assert Layered.Fields["activeLayer"] == 0
    Entries = MappingItems(Layered.Fields["layers"])
    assert tuple(Entry.First for Entry in Entries) == (2, 3)
    assert all(isinstance(Entry.Second, LocalRef) for Entry in Entries)
    Mapping, WoodNode = tuple(
        Graph.Resolve(Entry.Second, Layered.SegmentId) for Entry in Entries
    )
    assert (Mapping.ClassName, WoodNode.ClassName) == (
        "ASMTextureMapping",
        "ProceduralWoodTextureMapping",
    )
    assert len({Layered.ObjectId, Mapping.ObjectId, WoodNode.ObjectId}) == 3
    assert (
        sum(
            Graph.HasBase(MapNode, "TextureMapping") for MapNode in Graph.Nodes.values()
        )
        == 3
    )
    assert WoodNode.Fields["originInitilized"] is True
    assert PackValues(">ddd", *PointCoords(WoodNode.Fields["origin"])) == PackValues(
        ">ddd", *Origin
    )
    assert PointCoords(WoodNode.Fields["bordFaceAxis"]) == (0.0, 0.0, 0.0)
    for MapNode in (Layered, Mapping, WoodNode):
        assert MapNode.SegmentId == BodyNode.SegmentId
        assert PointCoords(MapNode.Fields["axis"]) == (0.0, 0.0, 0.0)
        assert MapNode.Fields["bakedTransformInGeometry"] == MatrixValue(None)
        assert MapNode.Fields["textureMappingTransform"] == MatrixValue(None)
        Bounds = ObjectFields(MapNode.Fields["textureMappingBoundingBox"])
        assert tuple(Bounds) == ("max", "min")
        assert PointCoords(Bounds["max"]) == (-FloatLimits.max,) * 3
        assert PointCoords(Bounds["min"]) == (FloatLimits.max,) * 3
