from pathlib import Path
from dataclasses import replace as CopyData

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSide.Admission.ChangeDualAux import (
    ChangeDualAux,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# material and appearance failures cannot pass merely because saved geometry still matches
@MarkTests.parametrize("ModeName", ("appearance", "material", "visual"))
def CheckDualAux(TmpPath: Path, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    DataValue = Sample.Source.read_bytes()
    Model = ChangeDualAux(ReadDocument(DataValue), ModeName)
    Container = CopyData(
        ReadContainer(DataValue),
        Streams=tuple(EmitDocSegment(Segment) for Segment in Model.Segments),
    )
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(EmitContainer(Container))
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
