from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


def ListSurface(Value: TsplineSurf | SubtypeRef) -> tuple[tuple[str, int | None], ...]:
    if isinstance(Value, SubtypeRef):
        return (("t_spl_sur", Value.Index),)
    Subtrans = Value.Subtrans
    Index = Subtrans.Index if isinstance(Subtrans, SubtypeRef) else None
    return ("t_spl_sur", None), ("t_spl_subtrans_object", Index)
