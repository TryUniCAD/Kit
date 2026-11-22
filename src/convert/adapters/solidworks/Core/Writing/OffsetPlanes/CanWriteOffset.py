from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PlanOffPart import (
    PlanOffPart,
)
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.Features.FeatureKinds import RefPlaneFeature
from interchange.document.Models.DocumentModel import CadDocument


# a fresh offset plane boss selects its own preparation instead of falling through to a different part family
def HasOffsetWrite(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.brep is None
        and len(DocumentValue.feature_timeline) == 2
        and type(DocumentValue.feature_timeline[0].definition) is RefPlaneFeature
    )


# target discovery checks the actual offset sketch and both supports before opening a staging transaction
def CanWriteOffset(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        PlanValue, _ = PlanOffPart(DocumentValue)
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return IsPartTarget(PlanValue.NameValue, TargetValue)
