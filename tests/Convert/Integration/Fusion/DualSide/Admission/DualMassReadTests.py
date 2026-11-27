from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# strict sdk admission must validate every stored tensor component after full archive encoding
@MarkTests.parametrize(
    "FieldName,AxisName",
    (
        ("volume", ""),
        ("area", ""),
        ("cog", "x"),
        ("cog", "y"),
        ("cog", "z"),
        ("moi", "x"),
        ("moi", "y"),
        ("moi", "z"),
        ("moiOffDiag", "x"),
        ("moiOffDiag", "y"),
        ("moiOffDiag", "z"),
    ),
)
def CheckMassBad(TmpPath: Path, FieldName: str, AxisName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model = ReadDocument(Sample.Source.read_bytes())
    Context = SelectExtrusion(BuildGraph(Model))
    Cache = Context.BodyNode.Fields["cache"]
    assert isinstance(Cache, ValueObject)
    Model = ChangeField(
        Model,
        Context.BodyNode.ObjectId,
        "cache",
        ChangeDualMass(Cache, FieldName, AxisName),
    )
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
