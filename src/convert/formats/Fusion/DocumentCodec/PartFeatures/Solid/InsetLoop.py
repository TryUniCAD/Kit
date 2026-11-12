from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanHeading,
)


def InsetJoint(
    Before: KPlaneSpan, After: KPlaneSpan, AmountCm: float
) -> tuple[float, float]:
    Corner = SpanFinish(Before)
    InwardX, InwardY = SpanHeading(Before, True)
    OutwardX, OutwardY = SpanHeading(After, False)
    Cross = InwardX * OutwardY - InwardY * OutwardX
    if abs(Cross) < 1e-9 and InwardX * OutwardX + InwardY * OutwardY > 0:
        return (Corner[0] - InwardY * AmountCm, Corner[1] + InwardX * AmountCm)
    if not isinstance(Before, LineSpan) or not isinstance(After, LineSpan):
        raise ValueError("Fusion part shell corners must join straight sides")
    StartX, StartY = Corner[0] - InwardY * AmountCm, Corner[1] + InwardX * AmountCm
    OtherX, OtherY = Corner[0] - OutwardY * AmountCm, Corner[1] + OutwardX * AmountCm
    Along = ((OtherX - StartX) * OutwardY - (OtherY - StartY) * OutwardX) / Cross
    return (StartX + InwardX * Along, StartY + InwardY * Along)


def InsetSpan(
    Value: KPlaneSpan,
    Start: tuple[float, float],
    Finish: tuple[float, float],
    AmountCm: float,
    Label: FaceLabel,
) -> KPlaneSpan:
    if isinstance(Value, LineSpan):
        HeadX, HeadY = SpanHeading(Value, False)
        if (Finish[0] - Start[0]) * HeadX + (Finish[1] - Start[1]) * HeadY <= 1e-9:
            raise ValueError("Fusion part shell thickness consumes a profile side")
        return LineSpan(Finish, Start, Label)
    Radius = (
        Value.RadiusCm - AmountCm if Value.SweepAngle > 0 else Value.RadiusCm + AmountCm
    )
    if Radius <= 1e-9:
        raise ValueError("Fusion part shell thickness consumes a profile arc")
    return ArcSpan(
        Value.CenterCm,
        Radius,
        Value.StartAngle + Value.SweepAngle,
        -Value.SweepAngle,
        Label,
    )


def InsetLoop(LoopValue: KPlaneLoop, AmountCm: float, Operation: int) -> KPlaneLoop:
    Joints = [
        InsetJoint(Value, LoopValue[(Index + 1) % len(LoopValue)], AmountCm)
        for Index, Value in enumerate(LoopValue)
    ]
    Spans = [
        InsetSpan(
            Value,
            Joints[Index - 1],
            Joints[Index],
            AmountCm,
            FaceLabel(Value.Label.PrimaryId, Value.Label.OperationIds + (Operation,)),
        )
        for Index, Value in enumerate(LoopValue)
    ]
    return tuple(reversed(Spans))
