from collections.abc import Mapping

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.Sketch import Sketch


# portable standard sweeps require two actual distinct sketch links before adapters consider supported shapes
def GetSweepErrs(
    StepValue: FeatureStep, Definition: SweepFeature, Sketches: Mapping[str, Sketch]
) -> tuple[str, ...]:
    if StepValue.kind != FeatureKind.KSweep:
        return (f"sweep definition on non-sweep feature {StepValue.id}",)
    SectionId = StepValue.sketch_id
    PathId = Definition.PathSketchId
    if SectionId is None or SectionId not in Sketches:
        return (f"sweep {StepValue.id} requires an actual section sketch",)
    if PathId not in Sketches or PathId == SectionId:
        return (f"sweep {StepValue.id} requires a distinct actual path sketch",)
    if not all(
        any(not Entity.construction for Entity in Sketches[Identity].entities)
        for Identity in (SectionId, PathId)
    ):
        return (f"sweep {StepValue.id} requires section and path geometry",)
    return ()
