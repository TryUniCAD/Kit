from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import CheckIdentity
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from interchange.geometry.Models.Transform import KTransformIdentity, Transform


# snapshot geometry must use the independently qualified source frame rather than an unchecked caller placement
def CheckSnapFrame(
    Graph: NativeGraph, Context: ExtrudeContext, Frame: Transform
) -> None:
    Saved = Context.Plane.Fields["transform"]
    if Frame == KTransformIdentity:
        CheckIdentity(Saved)
    else:
        if not isinstance(Saved, MatrixValue) or Saved.Entries is None:
            raise ValueError("Dual snapshot requires its actual selected source frame")
        SameNumbers(
            Saved.Entries,
            (
                Frame.x_axis.x,
                Frame.y_axis.x,
                Frame.z_axis.x,
                Frame.origin.x / 10,
                Frame.x_axis.y,
                Frame.y_axis.y,
                Frame.z_axis.y,
                Frame.origin.y / 10,
                Frame.x_axis.z,
                Frame.y_axis.z,
                Frame.z_axis.z,
                Frame.origin.z / 10,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        )
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    if Frame == KTransformIdentity:
        CheckIdentity(Matrix.Fields["matrix3d"])
    elif Matrix.Fields["matrix3d"] != Saved:
        raise ValueError(
            "Dual snapshot source coordinate system and owned matrix disagree"
        )
    CheckIdentity(Context.Sketch.Fields["occurrenceTransform"])
