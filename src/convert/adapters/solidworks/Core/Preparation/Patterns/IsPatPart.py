from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import LinearPattern


# the pattern profile must be selected before any broader part preparation branch
def IsPatPart(DocumentValue: CadDocument) -> bool:
    Timeline = DocumentValue.feature_timeline
    return len(Timeline) == 5 and type(Timeline[-1].definition) is LinearPattern
