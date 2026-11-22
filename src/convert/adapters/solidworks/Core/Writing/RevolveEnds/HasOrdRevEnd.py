from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.document.Models.DocumentModel import CadDocument


# the measured end batch owns one ordinary typed boss rather than thin or selected cut histories
def HasOrdRevEnd(DocumentValue: CadDocument) -> bool:
    Features = DocumentValue.feature_timeline
    return len(Features) == 1 and type(Features[0].definition) is AngularRevolve
