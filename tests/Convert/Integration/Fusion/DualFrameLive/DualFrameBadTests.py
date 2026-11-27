from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from hashlib import sha256 as HashBytes
from dataclasses import replace as ReplaceData
from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import (
    ReadDualFrame,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.DualFrameLive.ChangeFrameDoc import (
    ChangeFrameDoc,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


# each ownership counterexample must survive native archive serialization before refusing the source frame
@MarkTests.parametrize(
    "CaseName",
    (
        "body_transform",
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
    ),
)
def CheckBadFrame(TmpPath: Path, CaseName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "frame")
    Model, _, _, _ = ReadTagSample(Sample)
    Payload = EmitParsed(ChangeFrameDoc(Model, CaseName))
    Target = TmpPath / "BadFrame.f3d"
    _ = Target.write_bytes(Payload)
    Sample = ReplaceData(Sample, Source=Target, Digest=HashBytes(Payload).hexdigest())
    Model, Graph, Context, Shape = ReadTagSample(Sample)
    with RaisesError((ValueError, TypeError)):
        FrameValue = ReadDualFrame(Graph, Context)
        _ = CheckDualLive(
            Graph,
            Context,
            Model,
            Shape,
            Sample.FirstMm,
            Sample.SecondMm,
            Sample.FirstTaper,
            Sample.SecondTaper,
            FrameValue,
        )
