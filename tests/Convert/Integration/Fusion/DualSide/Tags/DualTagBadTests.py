from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashBytes
from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagModel import ChangeTagModel
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


# malformed identities must refuse after actual native archive serialization and decoding
@MarkTests.parametrize(
    "CaseName",
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
def CheckBadTags(TmpPath: Path, CaseName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model, Graph, Context, Shape = ReadTagSample(Sample)
    Changed = ChangeTagModel(Model, Sample, CaseName)
    Payload = EmitParsed(Changed)
    Target = TmpPath / "BadTags.f3d"
    _ = Target.write_bytes(Payload)
    Sample = ReplaceData(Sample, Source=Target, Digest=HashBytes(Payload).hexdigest())
    with RaisesError(ValueError):
        Model, Graph, Context, Shape = ReadTagSample(Sample)
        _ = CheckDualLive(
            Graph,
            Context,
            Model,
            Shape,
            Sample.FirstMm,
            Sample.SecondMm,
            Sample.FirstTaper,
            Sample.SecondTaper,
        )
