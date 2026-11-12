from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeKnots import MakeKnots
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakePoints import (
    MakePoints,
)


def MakeNubsSurf(Value: NubsSurface) -> tuple[KAsmToken, ...]:
    KnotsU = MakeKnots(Value.KnotsU)
    KnotsV = MakeKnots(Value.KnotsV)
    return (
        (13, "nubs"),
        (4, Value.DegreeU),
        (4, Value.DegreeV),
        (21, Value.ClosureU),
        (21, Value.ClosureV),
        (21, Value.SingularU),
        (21, Value.SingularV),
        KnotsU[0],
        KnotsV[0],
        *KnotsU[1:],
        *KnotsV[1:],
        *MakePoints(Value.Points),
    )
