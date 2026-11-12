from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSurface import ListSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode


def ListSubtypes(Value: KJournalEntity) -> tuple[tuple[str, int | None], ...]:
    if isinstance(Value, SplineNode):
        return ListSurface(Value.Surface)
    if isinstance(Value, IntcurveNode):
        return (("exact_int_cur", None),)
    if isinstance(Value, PcurveNode):
        return ("exp_par_cur", None), *ListSurface(Value.Curve.Support)
    return ()
