from convert.adapters.Fusion.Native.Cuts.CutSideLabels import CutSideLabels
from convert.adapters.Fusion.Native.Cuts.SideTagFor import SideTagFor
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from interchange.geometry.Models.VectorPlane import PlaneVector


# cap ownership stays with the stock while new sides preserve the modifying feature operation
def MakeCutLabels(
    Graph: NativeGraph,
    Contexts: tuple[ExtrudeContext, ExtrudeContext],
    Shapes: tuple[RectGeometry, RectGeometry],
    Outline: tuple[PlaneVector, ...],
    Operations: dict[int, tuple[int, ...]],
) -> tuple[FeatureTag, ...]:
    Owned = tuple(Operations[Context.Extrude.ObjectId] for Context in Contexts)
    if any(not Values for Values in Owned):
        raise ValueError("Native corner cut requires one operation per extrusion")
    Labels = (
        CutSideLabels(Graph, Contexts[0], Shapes[0], Owned[0][0], True),
        CutSideLabels(Graph, Contexts[1], Shapes[1], Owned[1][0], False),
    )
    return (
        FeatureTag("1", Owned[0][:1]),
        FeatureTag("2", Owned[0][:1]),
        *(
            SideTagFor(First, Outline[(Index + 1) % len(Outline)], Shapes, Labels)
            for Index, First in enumerate(Outline)
        ),
    )
