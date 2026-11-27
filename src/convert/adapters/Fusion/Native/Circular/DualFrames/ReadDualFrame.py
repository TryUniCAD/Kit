from convert.adapters.Fusion.Native.Circular.DualFrames.CheckFrameOwn import (
    CheckFrameOwn,
)
from convert.adapters.Fusion.Native.Circular.DualFrames.CheckFrameRef import (
    CheckFrameRef,
)
from convert.adapters.Fusion.Native.Circular.DualFrames.ReadFrameBasis import (
    ReadFrameBasis,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from interchange.geometry.Models.Transform import Transform


# source selected principal frames must be proved before public geometry changes coordinate systems
def ReadDualFrame(Graph: NativeGraph, Context: ExtrudeContext) -> Transform:
    Matrix, Reference, Datum = CheckFrameRef(Graph, Context)
    CheckFrameOwn(Graph, Context, Matrix, Reference)
    Frame = ReadFrameBasis(Context.Plane, Matrix, Datum)
    SameNumbers(
        PointCoords(Context.Extrude.Fields["profileNormal"]),
        (Frame.z_axis.x, Frame.z_axis.y, Frame.z_axis.z),
    )
    return Frame
