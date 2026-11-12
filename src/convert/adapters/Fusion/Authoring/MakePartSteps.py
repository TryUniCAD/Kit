from convert.adapters.Fusion.Authoring.MakePartParams import DrivingLength
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep

KStepKinds: dict[type[object], FeatureKind] = {
    FilletSpec: FeatureKind.KFillet,
    ChamferSpec: FeatureKind.KChamfer,
    ExtrudeSpec: FeatureKind.KExtrusion,
    HoleSpec: FeatureKind.KHole,
    PatternSpec: FeatureKind.KPattern,
    CircularSpec: FeatureKind.KPattern,
    MirrorSpec: FeatureKind.KMirror,
    PlaneSpec: FeatureKind.KReference,
}


def StepKind(Feature: KPartFeature) -> FeatureKind:
    return KStepKinds.get(type(Feature), FeatureKind.KShell)


def MakePartSteps(SpecValue: DocumentSpec) -> tuple[FeatureStep, ...]:
    Steps: list[FeatureStep] = []
    Previous = "extrude"
    for Index, Feature in enumerate(SpecValue.Features):
        Identity = "feature" + str(Index + 1)
        Owned = () if DrivingLength(Feature) is None else (Identity + "-amount",)
        Steps.append(
            FeatureStep(
                Identity,
                Feature.FeatureName,
                StepKind(Feature),
                Index + 2,
                (Previous,),
                parameter_ids=Owned,
            )
        )
        Previous = Identity
    return tuple(Steps)
