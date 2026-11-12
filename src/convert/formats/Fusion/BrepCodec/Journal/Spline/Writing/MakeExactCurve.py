from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.ExactCurve import ExactCurve
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeJumps import MakeJumps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeNubsCurve import (
    MakeNubsCurve,
)


def MakeExactCurve(Value: ExactCurve) -> tuple[KAsmToken, ...]:
    return (
        (15, None),
        (13, "exact_int_cur"),
        (4, Value.Revision),
        (21, 0),
        *MakeNubsCurve(Value.Cache),
        (6, Value.FitTolerance),
        (13, "null_surface"),
        (13, "null_surface"),
        (13, "nullbs"),
        (13, "nullbs"),
        *(Field for Bound in Value.CacheBounds for Field in MakeBound(Bound)),
        *MakeJumps(Value.Jumps),
        (4, Value.Extension),
        *(Field for Bound in Value.Ranges for Field in MakeBound(Bound)),
        (21, Value.TailCodes[0]),
        (21, Value.TailCodes[1]),
        (16, None),
    )
