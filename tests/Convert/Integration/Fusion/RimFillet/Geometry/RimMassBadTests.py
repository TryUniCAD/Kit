from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimMass import CheckRimMass
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)


# each stale mass field must refuse after full native archive serialization and parsing
@MarkTests.parametrize(
    "FieldName, AxisName",
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
def CheckBadRimMass(TmpPath: Path, FieldName: str, AxisName: str) -> None:
    Sample = next(
        Value for Value in ReadPolicyCases() if Value.CaseName == "source-discovery-01"
    )
    Model = ReadDocument(Sample.Source.read_bytes())
    Context = ReadRimContext(BuildGraph(Model))
    Cache = Context.Extrusion.BodyNode.Fields["cache"]
    assert isinstance(Cache, ValueObject)
    Changed = ChangeField(
        Model,
        Context.Extrusion.BodyNode.ObjectId,
        "cache",
        ChangeDualMass(Cache, FieldName, AxisName),
    )
    Payload = EmitParsed(Changed)
    Target = TmpPath / "MalformedMass.f3d"
    _ = Target.write_bytes(Payload)
    Model = ReadDocument(Target.read_bytes())
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    Shape = ReadCircle(Graph, Context.Extrusion)
    with RaisesError(ValueError, match="mass cache"):
        CheckRimMass(
            Context,
            Shape.Geometry.radius,
            NumberValue(Context.Extrusion.Along.Fields["value"]) * 10,
            NumberValue(Context.Radius.Fields["value"]) * 10,
        )
