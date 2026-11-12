from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep


def MakePartSteps(SpecValue: DocumentSpec) -> tuple[FeatureStep, ...]:
    Steps: list[FeatureStep] = []
    Previous = "extrude"
    for Index, Feature in enumerate(SpecValue.Features):
        Identity = "feature" + str(Index + 1)
        if isinstance(Feature, FilletSpec):
            KindValue = FeatureKind.KFillet
        elif isinstance(Feature, ChamferSpec):
            KindValue = FeatureKind.KChamfer
        else:
            KindValue = FeatureKind.KShell
        Steps.append(
            FeatureStep(
                Identity,
                Feature.FeatureName,
                KindValue,
                Index + 2,
                (Previous,),
                parameter_ids=(Identity + "-amount",),
            )
        )
        Previous = Identity
    return tuple(Steps)
