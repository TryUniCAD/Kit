from convert.adapters.Fusion.Native.FixedPrism.ReadFixedRect import ReadFixedRect
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode
from convert.adapters.Fusion.Native.Rectangle.ReadRectRules import ReadRectRules
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof


# distinct fixed and coincident anchor representations need their own strict semantic admission
def ReadPrismRules(
    Graph: NativeGraph, Context: ExtrudeContext, Reverse: bool, YzDatum: bool
) -> RectSketchProof | None:
    if not (Reverse or YzDatum) and len(Graph.ByClass("SketchGeomConstraint")) == 4:
        if ReadExtentMode(Context.Extrude) != "one_sided":
            raise ValueError("Native fixed rectangle requires a one sided extrusion")
        return ReadFixedRect(Graph, Context)
    return ReadRectRules(Graph, Context, Reverse, YzDatum)
