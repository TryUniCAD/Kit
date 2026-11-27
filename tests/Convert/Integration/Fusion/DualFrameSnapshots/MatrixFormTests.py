from pytest import mark as TestMark

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualFrameSnapshots.CheckFramedSnap import (
    CheckFramedSnap,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# equivalent explicit identity storage must retain the previous default placement contract
@TestMark.parametrize("RoleName", ("ucs", "matrix"))
def CheckMatrixForm(RoleName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model = ReadDocument(Sample.Source.read_bytes())
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Owner = (
        Context.Plane
        if RoleName == "ucs"
        else ResolveField(
            Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
        )
    )
    FieldName = "transform" if RoleName == "ucs" else "matrix3d"
    Matrix = MatrixValue(
        (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    )
    Payload = EmitParsed(ChangeField(Model, Owner.ObjectId, FieldName, Matrix))
    CheckFramedSnap(Payload)
