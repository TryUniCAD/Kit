from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.BlockSolid import (
    BlockSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.EditCorner import (
    EditCorner,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.HollowSolid import (
    HollowSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def ApplyFeature(
    Solid: PrismSolid, Feature: KPartFeature, Operation: int
) -> PrismSolid:
    Label = FaceLabel("1", (Operation,))
    if isinstance(Feature, FilletSpec):
        Corner = (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0)
        return EditCorner(Solid, Corner, Feature.RadiusMm / 10.0, Label, True)
    if isinstance(Feature, ChamferSpec):
        Corner = (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0)
        return EditCorner(Solid, Corner, Feature.DistanceMm / 10.0, Label, False)
    return HollowSolid(Solid, Feature.ThicknessMm / 10.0, Operation)


def SolvePart(SpecValue: DocumentSpec) -> tuple[PrismSolid, tuple[PartStage, ...]]:
    Policy = AuthorPolicy()
    BaseValue = BlockSolid(
        SpecValue.WidthMm / 10.0,
        SpecValue.DepthMm / 10.0,
        SpecValue.LengthMm / 10.0,
        Policy,
    )
    Solid, Operation, StateId = (
        BaseValue,
        Policy.FirstOperationId + 3,
        Policy.HistoryCurrentId,
    )
    Counts: dict[str, int] = {}
    Stages: list[PartStage] = []
    for Feature in SpecValue.Features:
        RuleValue = FamilyOf(Feature)
        Counts[RuleValue.ClassName] = Counts.get(RuleValue.ClassName, 0) + 1
        After = ApplyFeature(Solid, Feature, Operation)
        Operations = tuple(range(Operation, Operation + RuleValue.OperationCount))
        StateId += 1
        Stages.append(
            PartStage(
                Feature, Solid, After, Operations, StateId, Counts[RuleValue.ClassName]
            )
        )
        Solid, Operation = After, Operation + RuleValue.OperationCount
    return BaseValue, tuple(Stages)
