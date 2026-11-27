from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashBytes
from pathlib import Path

from pytest import mark as MarkTests

from convert.adapters.Fusion.Native.Circular.DualFrames.CheckFrameRef import (
    CheckFrameRef,
)
from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import (
    ReadDualFrame,
)
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from interchange.geometry.Models.Transform import KTransformIdentity
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


# both legal identity spellings preserve existing source compatibility after actual native serialization
@MarkTests.parametrize("ChangeUcs", (False, True))
def CheckFrameForms(TmpPath: Path, ChangeUcs: bool) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Model, Graph, Context, _ = ReadTagSample(Sample)
    Matrix, _, _ = CheckFrameRef(Graph, Context)
    Model = ChangeField(
        Model,
        Context.Plane.ObjectId if ChangeUcs else Matrix.ObjectId,
        "transform" if ChangeUcs else "matrix3d",
        MatrixValue(None),
    )
    Model = ChangeField(
        Model,
        Matrix.ObjectId if ChangeUcs else Context.Plane.ObjectId,
        "matrix3d" if ChangeUcs else "transform",
        MatrixValue(
            tuple(float(First == Second) for First in range(4) for Second in range(4))
        ),
    )
    Payload = EmitParsed(Model)
    Target = TmpPath / "IdentityFrame.f3d"
    _ = Target.write_bytes(Payload)
    Sample = ReplaceData(Sample, Source=Target, Digest=HashBytes(Payload).hexdigest())
    Model, Graph, Context, Shape = ReadTagSample(Sample)
    assert ReadDualFrame(Graph, Context) == KTransformIdentity
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
