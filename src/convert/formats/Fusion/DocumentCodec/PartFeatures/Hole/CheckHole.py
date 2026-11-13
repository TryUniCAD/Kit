from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import IsNumber
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec


def IsBored(Feature: HoleSpec) -> bool:
    return Feature.BoreDiameterMm > 0 or Feature.BoreDepthMm > 0


def CheckHole(Feature: HoleSpec) -> None:
    Center = CastValue(object, Feature.CenterMm)
    if not isinstance(Center, tuple) or len(Feature.CenterMm) != 2:
        raise ValueError("Fusion hole centers require two planar coordinates")
    Amounts = (Feature.DiameterMm, Feature.DepthMm, Feature.BoreDiameterMm)
    Numbers = (*Feature.CenterMm, *Amounts, Feature.BoreDepthMm)
    if not all(IsNumber(Value) for Value in Numbers):
        raise ValueError("Fusion hole values must be finite numbers")
    if Feature.DiameterMm <= 0 or min(Numbers[3:]) < 0:
        raise ValueError("Fusion hole sizes must be positive")
    if not IsBored(Feature):
        return
    if Feature.BoreDiameterMm <= Feature.DiameterMm or Feature.BoreDepthMm <= 0:
        raise ValueError("Fusion counterbores need a wider diameter and a depth")
    if Feature.DepthMm and Feature.BoreDepthMm >= Feature.DepthMm:
        raise ValueError("Fusion counterbores must be shallower than the hole")
