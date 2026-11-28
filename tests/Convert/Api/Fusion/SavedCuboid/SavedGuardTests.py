from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField, ChangeNative
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# strict admission must reject unsupported native changes before any neutral success claim is possible
@MarkTests.parametrize(
    "ChangeName",
    ("suppression", "direction", "parameter", "formula", "owner", "anchor", "axis"),
)
def TestSavedGuard(ChangeName: str) -> None:
    Model = ReadDocument(SavedSource(KSavedCases[1]).read_bytes())
    Graph = BuildGraph(Model)
    if ChangeName == "anchor":
        Anchor = next(
            Value
            for Value in Graph.ByClass("Point3D")
            if Value.Fields["isFixed"] and not Value.Fields["isOrigin"]
        )
        Changed = ChangeField(Model, Anchor.ObjectId, "isFixed", False)
    elif ChangeName == "axis":
        AxisRule = Graph.ByClass("SketchGeomConstraint")[0]
        Changed = ChangeField(Model, AxisRule.ObjectId, "constraintType", 1)
    else:
        Changed = ChangeNative(Model, ChangeName)
    Payload = EmitParsed(Changed)
    with RaisesError(ValueError):
        _ = OpenDocument(Payload, source_format="f3d")
