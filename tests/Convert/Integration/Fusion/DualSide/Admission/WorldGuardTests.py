from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualFrameLive.ChangeFrameDoc import ChangeFrameDoc
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# source matrix ownership and body placement corruption must refuse through the public sdk
@MarkTests.parametrize(
    "ModeName",
    (
        "ucs_matrix",
        "definition_matrix",
        "occurrence_matrix",
        "datum_name",
        "datum_origin",
        "datum_owner",
        "definition_owner",
        "definition_active",
        "definition_inferred",
        "reference_scope",
        "update_owner",
        "update_health",
        "instance_owner",
        "body_transform",
    ),
)
def CheckWorldBad(TmpPath: Path, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "frame")
    Model = ReadDocument(Sample.Source.read_bytes())
    Payload = EmitParsed(ChangeFrameDoc(Model, ModeName))
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(Payload)
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
