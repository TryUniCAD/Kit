from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def ListPrograms(Entities: tuple[KJournalEntity, ...]) -> tuple[TsplineSurface, ...]:
    Supports = tuple(
        Value.Surface if isinstance(Value, SplineNode) else Value.Curve.Support
        for Value in Entities
        if isinstance(Value, (SplineNode, PcurveNode))
    )
    return tuple(
        Support.Subtrans.Surface
        for Support in Supports
        if isinstance(Support, TsplineSurf)
        and isinstance(Support.Subtrans, SubtransNode)
    )
