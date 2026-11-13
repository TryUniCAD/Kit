from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import (
    CheckExtrude,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.CheckHole import CheckHole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.CheckCopy import (
    CheckCopy,
)

KFeatureLimit = 16
KCornerLimit = 8
KLinkedSpecs = (PatternSpec, CircularSpec, MirrorSpec, PlaneSpec)


def FeatureAmounts(Feature: KPartFeature) -> tuple[object, ...]:
    if isinstance(Feature, FilletSpec):
        return (*Feature.CornerMm, Feature.RadiusMm)
    if isinstance(Feature, ChamferSpec):
        return (*Feature.CornerMm, Feature.DistanceMm)
    if isinstance(Feature, ShellSpec):
        return (Feature.ThicknessMm,)
    return ()


def CheckName(NameValue: object) -> None:
    if (
        not isinstance(NameValue, str)
        or not NameValue
        or len(NameValue) > 1024
        or "\x00" in NameValue
    ):
        raise ValueError("Invalid Fusion part feature name")


def CheckPair(Point: object) -> None:
    if not isinstance(Point, tuple):
        raise ValueError("Fusion part corners require two planar coordinates")
    Coordinates = CastValue(tuple[object, ...], Point)
    if len(Coordinates) != 2:
        raise ValueError("Fusion part corners require two planar coordinates")
    for Value in Coordinates:
        if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
            raise ValueError("Fusion part feature values must be finite numbers")


def CheckCorners(Feature: FilletSpec | ChamferSpec) -> None:
    Extras = CastValue(object, Feature.MoreCornersMm)
    if not isinstance(Extras, tuple):
        raise ValueError("Fusion corner edits require a tuple of corners")
    Points = CastValue(tuple[object, ...], Extras)
    if len(Points) >= KCornerLimit:
        raise ValueError("Fusion corner edits take at most eight corners")
    for Point in Points:
        CheckPair(Point)
    Corners = (Feature.CornerMm, *Feature.MoreCornersMm)
    if len(set(Corners)) != len(Corners):
        raise ValueError("Fusion corner edits require distinct corners")


def CheckBevel(Feature: ChamferSpec) -> None:
    Extras = (
        CastValue(object, Feature.SecondMm),
        CastValue(object, Feature.AngleDegrees),
    )
    for Value in Extras:
        if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
            raise ValueError("Fusion chamfer values must be finite numbers")
    if min(Feature.SecondMm, Feature.AngleDegrees) < 0:
        raise ValueError("Fusion chamfer values must not be negative")
    if min(Feature.SecondMm, Feature.AngleDegrees) > 0 or Feature.AngleDegrees >= 90:
        raise ValueError("Fusion chamfers take a second distance or an acute angle")


def CheckFeature(Feature: KPartFeature) -> None:
    _ = FamilyOf(Feature)
    if isinstance(Feature, ExtrudeSpec):
        CheckExtrude(Feature)
        return
    CheckName(CastValue(object, Feature.FeatureName))
    if isinstance(Feature, HoleSpec):
        CheckHole(Feature)
        return
    if isinstance(Feature, (AxisSpec, PointSpec)):
        CheckPair(CastValue(object, Feature.CornerMm))
        return
    if isinstance(Feature, KLinkedSpecs):
        return
    Amounts = FeatureAmounts(Feature)
    if not isinstance(Feature, ShellSpec) and len(Amounts) != 3:
        raise ValueError("Fusion part corners require two planar coordinates")
    for Amount in Amounts:
        if type(Amount) not in (int, float) or not IsFinite(CastValue(float, Amount)):
            raise ValueError("Fusion part feature values must be finite numbers")
    if CastValue(float, Amounts[-1]) <= 0:
        raise ValueError("Fusion part feature sizes must be positive")
    if isinstance(Feature, (FilletSpec, ChamferSpec)):
        CheckCorners(Feature)
    if isinstance(Feature, ChamferSpec):
        CheckBevel(Feature)


def IsNewBody(Feature: KPartFeature) -> bool:
    return isinstance(Feature, ExtrudeSpec) and Feature.Operation == "new"


def CheckOrder(SpecValue: DocumentSpec) -> None:
    Features = SpecValue.Features
    Fresh = [Index for Index, Feature in enumerate(Features) if IsNewBody(Feature)]
    Expected = [0] if SpecValue.ProfileKind == "part" else []
    if Fresh != Expected:
        raise ValueError("Fusion part bodies start with exactly one new extrude")
    for Index, Feature in enumerate(Features):
        if isinstance(Feature, ShellSpec) and Index != len(Features) - 1:
            raise ValueError("Fusion part shell must be the final feature")


def CheckFeatures(SpecValue: DocumentSpec) -> None:
    Features = CastValue(object, SpecValue.Features)
    if not isinstance(Features, tuple):
        raise ValueError("Fusion part features must be a tuple")
    if SpecValue.ProfileKind == "part" and not Features:
        raise ValueError("Fusion part documents require features")
    if not Features:
        return
    if SpecValue.ProfileKind not in ("cuboid", "part") or SpecValue.ConstrainRectangle:
        raise ValueError(
            "Fusion part features require a part or an unconstrained cuboid"
        )
    if len(SpecValue.Features) > KFeatureLimit:
        raise ValueError("Fusion part feature count exceeds the qualified limit")
    for Index, Feature in enumerate(SpecValue.Features):
        CheckFeature(Feature)
        CheckCopy(SpecValue.Features, Index)
    CheckOrder(SpecValue)
    NameValue = SpecValue.ParamName
    if NameValue.startswith("d") and NameValue[1:].isdigit():
        raise ValueError("Fusion part features reserve generated parameter names")
