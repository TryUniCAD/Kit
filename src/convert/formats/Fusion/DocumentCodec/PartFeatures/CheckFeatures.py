from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

KFeatureLimit = 16


def FeatureAmounts(Feature: KPartFeature) -> tuple[object, ...]:
    if isinstance(Feature, FilletSpec):
        return (*Feature.CornerMm, Feature.RadiusMm)
    if isinstance(Feature, ChamferSpec):
        return (*Feature.CornerMm, Feature.DistanceMm)
    return (Feature.ThicknessMm,)


def CheckFeature(Feature: KPartFeature) -> None:
    _ = FamilyOf(Feature)
    Amounts = FeatureAmounts(Feature)
    if not isinstance(Feature, ShellSpec) and len(Amounts) != 3:
        raise ValueError("Fusion part corners require two planar coordinates")
    for Amount in Amounts:
        if type(Amount) not in (int, float) or not IsFinite(CastValue(float, Amount)):
            raise ValueError("Fusion part feature values must be finite numbers")
    if CastValue(float, Amounts[-1]) <= 0:
        raise ValueError("Fusion part feature sizes must be positive")
    NameValue = CastValue(object, Feature.FeatureName)
    if (
        not isinstance(NameValue, str)
        or not NameValue
        or len(NameValue) > 1024
        or "\x00" in NameValue
    ):
        raise ValueError("Invalid Fusion part feature name")


def CheckFeatures(SpecValue: DocumentSpec) -> None:
    Features = CastValue(object, SpecValue.Features)
    if not isinstance(Features, tuple):
        raise ValueError("Fusion part features must be a tuple")
    if not Features:
        return
    if SpecValue.ProfileKind != "cuboid" or SpecValue.ConstrainRectangle:
        raise ValueError("Fusion part features require an unconstrained cuboid")
    if len(SpecValue.Features) > KFeatureLimit:
        raise ValueError("Fusion part feature count exceeds the qualified limit")
    for Index, Feature in enumerate(SpecValue.Features):
        CheckFeature(Feature)
        if isinstance(Feature, ShellSpec) and Index != len(SpecValue.Features) - 1:
            raise ValueError("Fusion part shell must be the final feature")
    NameValue = SpecValue.ParamName
    if NameValue.startswith("d") and NameValue[1:].isdigit():
        raise ValueError("Fusion part features reserve generated parameter names")
