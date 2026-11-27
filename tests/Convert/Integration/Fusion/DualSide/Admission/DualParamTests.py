from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSide.Admission.ChangeDualParam import (
    ChangeDualParam,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# the public sdk must reject encoded ownership unit expression and allocator counterexamples
@MarkTests.parametrize(
    "ModeName",
    ("role", "unit", "expression", "reciprocal", "owner", "allocation", "operation"),
)
def CheckDualParam(TmpPath: Path, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model = ReadDocument(Sample.Source.read_bytes())
    Payload = EmitParsed(ChangeDualParam(Model, ModeName))
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(Payload)
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
