from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# dimension axis dispatch must still reject duplicate axis and duplicate driver identities
@MarkTests.parametrize("FieldName", ("constraintType", "dcParameter"))
def TestDupDim(FieldName: str) -> None:
    Model = ReadDocument(SavedSource(KSavedCases[1]).read_bytes())
    First, Second = BuildGraph(Model).ByClass("FusionSketchLinearDim")
    Changed = ChangeField(Model, Second.ObjectId, FieldName, First.Fields[FieldName])
    Expected = (
        "one dimension on each axis"
        if FieldName == "constraintType"
        else "ownership collection disagrees"
    )
    with RaisesError(ValueError, match=Expected):
        _ = OpenDocument(EmitParsed(Changed), source_format="f3d")
