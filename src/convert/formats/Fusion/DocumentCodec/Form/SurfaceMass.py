from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    SurfaceFrame,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SurfacePoint import (
    SurfacePoint,
)
from convert.formats.Fusion.DocumentCodec.Form.IntegrationRules import (
    KGaussRule,
    KPowerMap,
)
from convert.formats.Fusion.DocumentCodec.Form.MassAccum import MassAccumMut
from convert.formats.Fusion.DocumentCodec.Form.VectorMath import CrossProduct


def SurfaceMass(Surface: NubsSurface) -> dict[str, float]:
    Total = dict.fromkeys(("area", "volume", *KPowerMap), 0.0)
    KnotsU = tuple(Value.Value for Value in Surface.KnotsU)
    KnotsV = tuple(Value.Value for Value in Surface.KnotsV)
    for LowerU, UpperU in zip(KnotsU, KnotsU[1:], strict=False):
        for LowerV, UpperV in zip(KnotsV, KnotsV[1:], strict=False):
            for NodeU, WeightU in KGaussRule:
                for NodeV, WeightV in KGaussRule:
                    ParamU = (LowerU + UpperU + (UpperU - LowerU) * NodeU) / 2.0
                    ParamV = (LowerV + UpperV + (UpperV - LowerV) * NodeV) / 2.0
                    Scale = (
                        (UpperU - LowerU) * (UpperV - LowerV) * WeightU * WeightV / 4.0
                    )
                    Point = SurfacePoint(Surface, ParamU, ParamV)
                    Frame = SurfaceFrame(Surface, ParamU, ParamV)
                    Normal = CastValue(
                        KJournalVector,
                        tuple(Value * Scale for Value in CrossProduct(*Frame)),
                    )
                    MassAccumMut(Total, Point, Normal)
    return Total
