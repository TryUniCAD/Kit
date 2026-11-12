from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.ParCurve import ParCurve
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import LogicWord
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeNubsCurve import (
    MakeNubsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeTsplSurf import (
    MakeTsplSurf,
)


def MakeParCurve(Value: ParCurve) -> tuple[KAsmToken, ...]:
    return (
        (15, None),
        (13, "exp_par_cur"),
        *MakeNubsCurve(Value.Cache),
        (6, Value.FitTolerance),
        (13, "spline"),
        LogicWord(Value.SupportFlag),
        *MakeTsplSurf(Value.Support),
        *(Field for Bound in Value.Bounds for Field in MakeBound(Bound)),
        (16, None),
    )
