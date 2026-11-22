from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.SweepFeature import SweepFeature


# portable standard sweeps require two actual distinct sketch links before adapters consider supported shapes
def GetSweepErrs(
    StepValue: FeatureStep, Definition: SweepFeature, SketchIds: set[str]
) -> tuple[str, ...]:
    if StepValue.kind != FeatureKind.KSweep:
        return (f"sweep definition on non-sweep feature {StepValue.id}",)
    SectionId = StepValue.sketch_id
    PathId = Definition.PathSketchId
    if SectionId is None or SectionId not in SketchIds:
        return (f"sweep {StepValue.id} requires an actual section sketch",)
    if PathId not in SketchIds or PathId == SectionId:
        return (f"sweep {StepValue.id} requires a distinct actual path sketch",)
    return ()
