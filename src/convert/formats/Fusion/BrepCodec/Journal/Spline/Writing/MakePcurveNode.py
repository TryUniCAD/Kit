from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import LogicWord
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeParCurve import (
    MakeParCurve,
)


def MakePcurveNode(Value: PcurveNode) -> AsmRecord:
    return AsmRecord(
        "pcurve",
        (
            *MakePrefix(Value.Prefix),
            (4, 0),
            LogicWord(Value.Reversed),
            *MakeParCurve(Value.Curve),
            (6, Value.OffsetU),
            (6, Value.OffsetV),
        ),
    )
