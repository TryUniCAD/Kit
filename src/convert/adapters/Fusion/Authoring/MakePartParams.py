from convert.adapters.Fusion.Authoring.MakeParams import MakeLength
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from interchange.records.RecordParameter import Parameter


def MakePartParams(SpecValue: DocumentSpec) -> tuple[Parameter, ...]:
    Values: list[Parameter] = []
    for Index, Feature in enumerate(SpecValue.Features):
        Identity = "feature" + str(Index + 1)
        if isinstance(Feature, FilletSpec):
            NameValue, Amount = "Radius", Feature.RadiusMm
        elif isinstance(Feature, ChamferSpec):
            NameValue, Amount = "Distance", Feature.DistanceMm
        else:
            NameValue, Amount = "innerThickness", Feature.ThicknessMm
        Values.append(MakeLength(Identity + "-amount", NameValue, Amount, Identity))
    return tuple(Values)
