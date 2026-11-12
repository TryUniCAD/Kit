from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


def MakeRefScope(Value: SubtypeRef) -> tuple[KAsmToken, ...]:
    return (15, None), (13, "ref"), (4, Value.Index), (16, None)
