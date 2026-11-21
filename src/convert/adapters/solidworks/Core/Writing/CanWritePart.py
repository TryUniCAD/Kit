from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Writing.CanWritePat import CanWritePat
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.document.Models.DocumentModel import CadDocument


# part selection must use the pattern compiler before the existing import and other native profiles
def CanWritePart(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    if IsPatPart(DocumentValue):
        return CanWritePat(DocumentValue, TargetValue)
    try:
        if DocumentValue.brep is not None:
            _ = PlanImportPart(DocumentValue, TargetValue)
            return True
        PlanValue = PlanNativePart(DocumentValue)
    except (TypeError, ValueError):
        return False
    return IsPartTarget(PlanValue.NameValue, TargetValue)
