from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashBytes
from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Integration.Fusion.DualSide.CheckDualNative import CheckDualNative
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# every persisted mass component must refuse stale values through actual encoded archives
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
def CheckBadMass(TmpPath: Path, FieldName: str, AxisName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model = ReadDocument(Sample.Source.read_bytes())
    Context = SelectExtrusion(BuildGraph(Model))
    Cache = Context.BodyNode.Fields["cache"]
    assert isinstance(Cache, ValueObject)
    Changed = ChangeField(
        Model,
        Context.BodyNode.ObjectId,
        "cache",
        ChangeDualMass(Cache, FieldName, AxisName),
    )
    Target = TmpPath / "Corrupt.f3d"
    Payload = EmitParsed(Changed)
    _ = Target.write_bytes(Payload)
    Sample = ReplaceData(Sample, Source=Target, Digest=HashBytes(Payload).hexdigest())
    Geometry = BuildDualSide(
        Sample.Identity,
        Sample.Frame,
        Sample.Profile,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )[0]
    with RaisesError(ValueError, match="Native circular mass cache disagrees"):
        CheckDualNative(Sample, Geometry)
