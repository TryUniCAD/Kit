from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagModel import ChangeTagModel


# the public reader must refuse every encoded live operation attribution and source link corruption
@MarkTests.parametrize(
    "ModeName",
    (
        "side_operation",
        "joint_missing",
        "joint_reversed",
        "joint_label",
        "body_secondary",
        "body_operation",
        "cap_label",
        "rim_label",
        "attribute_chain",
        "extended_tag",
        "sketch_owner",
        "sketch_circle",
        "time_value",
        "body_uuid",
        "history_end",
        "allocator_owner",
    ),
)
def CheckDualTagBad(TmpPath: Path, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model = ReadDocument(Sample.Source.read_bytes())
    Payload = EmitParsed(ChangeTagModel(Model, Sample, ModeName))
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(Payload)
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
