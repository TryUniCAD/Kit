from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeKnots import MakeKnots
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakePoints import (
    MakePoints,
)


def MakeNubsCurve(Value: NubsCurve) -> tuple[KAsmToken, ...]:
    return (
        (13, "nubs"),
        (4, Value.Degree),
        (21, Value.Closure),
        *MakeKnots(Value.Knots),
        *MakePoints(Value.Points),
    )
