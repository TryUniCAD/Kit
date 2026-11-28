from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# the exact principal measurement applies to a fresh ordinary one sided angular feature
def HasPrincRev(DocumentValue: CadDocument) -> bool:
    if len(DocumentValue.feature_timeline) != 1:
        return False
    Definition = DocumentValue.feature_timeline[0].definition
    return isinstance(Definition, AngularRevolve) and Definition.SideMode == "one_sided"
