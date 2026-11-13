from dataclasses import replace as ReplaceValue
from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.HoleSolid import HoleSolid
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    FamilyOf,
    IsStateless,
    OperationsOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PatternSolid import (
    CopySolid,
    KCopySpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    PlanSketch,
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.BlockSolid import (
    BlockSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.EditCorner import (
    EditCorner,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.HollowSolid import (
    HollowSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ToolSlab import (
    ToolEdgeTags,
    ToolLabels,
    ToolSlab,
)

KBaseSketchTags = 9


def ApplyExtrude(
    Solid: PrismSolid | None, Feature: ExtrudeSpec, Operation: int, Sketched: SketchPlan
) -> PrismSolid:
    Shaper = ToolSlab(Feature, Operation + 1)
    Curves = tuple(
        (Label, Segment.CurveTag)
        for Label, Segment in zip(ToolLabels(Feature, Operation + 1), Sketched.Edges)
    )
    BodyLabel = FaceLabel(str(Operation + 1), (), len(Feature.Profile) + 3)
    Tagged = ToolEdgeTags(Feature, Operation + 1, Sketched.Edges[0].CurveTag)
    if Feature.Operation == "new":
        if Solid is not None:
            raise ValueError("Fusion part authoring supports one solid body")
        return PrismSolid((Shaper,), BodyLabel, Curves, Tagged)
    if Solid is None:
        raise ValueError("Fusion part extrude requires an existing body")
    Joined = BodyLabel if Feature.Operation == "join" else None
    Result = ExtrudeSolid(Solid, Shaper, Feature.Operation, Joined)
    return ReplaceValue(
        Result,
        SketchCurves=Solid.SketchCurves + Curves,
        EdgeTags=Solid.EdgeTags + Tagged,
    )


def CornerSolid(
    Solid: PrismSolid, Feature: FilletSpec | ChamferSpec, Operation: int
) -> PrismSolid:
    Rounded = isinstance(Feature, FilletSpec)
    if isinstance(Feature, FilletSpec):
        Amount, Bevel = Feature.RadiusMm / 10.0, (0.0, 0.0)
    else:
        Amount = Feature.DistanceMm / 10.0
        Bevel = (Feature.SecondMm / 10.0, Radians(Feature.AngleDegrees))
    for Index, CornerMm in enumerate((Feature.CornerMm, *Feature.MoreCornersMm)):
        Corner = (CornerMm[0] / 10.0, CornerMm[1] / 10.0)
        Label = FaceLabel(str(Index + 1), (Operation,))
        Solid = EditCorner(Solid, Corner, Amount, Label, Rounded, Bevel)
    return Solid


def ApplyFeature(
    Solid: PrismSolid | None, Feature: KPartFeature, Operation: int
) -> PrismSolid:
    if Solid is None:
        raise ValueError("Fusion part features require a body from a new extrude")
    if isinstance(Feature, (FilletSpec, ChamferSpec)):
        return CornerSolid(Solid, Feature, Operation)
    if isinstance(Feature, ExtrudeSpec):
        raise ValueError("Fusion part extrudes require a sketch plan")
    if isinstance(Feature, HoleSpec):
        return HoleSolid(Solid, Feature, Operation)
    if isinstance(Feature, PlaneSpec):
        return Solid
    if isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        raise ValueError("Fusion part copies require their source stage")
    return HollowSolid(Solid, Feature.ThicknessMm / 10.0, Operation)


def BaseSolid(SpecValue: DocumentSpec, Policy: AuthorPolicy) -> PrismSolid | None:
    if SpecValue.ProfileKind == "part":
        return None
    return BlockSolid(
        SpecValue.WidthMm / 10.0,
        SpecValue.DepthMm / 10.0,
        SpecValue.LengthMm / 10.0,
        Policy,
    )


def CopyContext(
    Features: tuple[KPartFeature, ...], Feature: KCopySpec, Index: int
) -> tuple[int, float]:
    if not isinstance(Feature, MirrorSpec):
        return Index, 0.0
    Plane = Features[Feature.PlaneIndex]
    if not isinstance(Plane, PlaneSpec) or Plane.BasePlane != "yz":
        raise ValueError("Fusion mirrors require an offset plane parallel to YZ")
    return Index, Plane.OffsetMm / 10.0


def StageSolid(
    Solid: PrismSolid | None,
    Feature: KPartFeature,
    Operation: int,
    Context: tuple[tuple[PartStage, ...], tuple[KPartFeature, ...], int],
) -> PrismSolid:
    Stages, Features, Index = Context
    if not isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        return ApplyFeature(Solid, Feature, Operation)
    if Solid is None:
        raise ValueError("Fusion part copies require an existing body")
    if not 0 <= Feature.SourceIndex < len(Stages):
        raise ValueError("Fusion part copies must follow their source feature")
    Source = Stages[Feature.SourceIndex]
    Extra = CopyContext(Features, Feature, Index)
    return CopySolid(Solid, Feature, Operation, Source, Extra)


def SolvePart(
    SpecValue: DocumentSpec,
) -> tuple[PrismSolid | None, tuple[PartStage, ...]]:
    Policy = AuthorPolicy()
    BaseValue = BaseSolid(SpecValue, Policy)
    IsPart = BaseValue is None
    Solid, Operation = BaseValue, Policy.FirstOperationId + (0 if IsPart else 3)
    StateId = Policy.HistoryCurrentId - (1 if IsPart else 0)
    NextTag = Policy.FirstSketchTag + (0 if IsPart else KBaseSketchTags)
    Counts: dict[str, int] = {"DcExtrudeFeature": 0 if IsPart else 1}
    Stages: list[PartStage] = []
    for Index, Feature in enumerate(SpecValue.Features):
        RuleValue = FamilyOf(Feature)
        Counts[RuleValue.ClassName] = Counts.get(RuleValue.ClassName, 0) + 1
        Sketched = None
        if isinstance(Feature, ExtrudeSpec):
            Sketched = PlanSketch(Feature.Profile, NextTag)
            NextTag = Sketched.NextTag
            After = ApplyExtrude(Solid, Feature, Operation, Sketched)
        else:
            Context = (tuple(Stages), SpecValue.Features, Index)
            After = StageSolid(Solid, Feature, Operation, Context)
        Count = OperationsOf(Feature)
        StateId += 0 if IsStateless(Feature) else 1
        Before = After if Solid is None else Solid
        Places = (tuple(range(Operation, Operation + Count)), StateId)
        Stages.append(
            PartStage(
                Feature, Before, After, *Places, Counts[RuleValue.ClassName], Sketched
            )
        )
        Solid, Operation = After, Operation + Count
    return BaseValue, tuple(Stages)
