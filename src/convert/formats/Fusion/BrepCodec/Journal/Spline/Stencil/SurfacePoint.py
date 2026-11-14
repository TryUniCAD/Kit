from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import (
    PointOnSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface


def SurfacePoint(Surface: NubsSurface, ParamU: float, ParamV: float) -> KJournalVector:
    Converted = BsSurface(
        bool(Surface.Weights),
        Surface.Form,
        Surface.DegreeU,
        Surface.DegreeV,
        Surface.ClosureU,
        Surface.ClosureV,
        Surface.SingularU,
        Surface.SingularV,
        tuple(Value.Value for Value in Surface.KnotsU),
        tuple(Value.Count for Value in Surface.KnotsU),
        tuple(Value.Value for Value in Surface.KnotsV),
        tuple(Value.Count for Value in Surface.KnotsV),
        Surface.Points,
        Surface.Weights,
    )
    return CastValue(KJournalVector, PointOnSurface(Converted, ParamU, ParamV))
