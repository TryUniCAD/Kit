from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsChmfPart import IsChmfPart
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    PlanChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Writing.CanWritePat import CanWritePat
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.document.Models.DocumentModel import CadDocument


# part selection must validate specific editable histories ahead of generic import and ordinary part routes
def CanWritePart(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        if IsChmfPart(DocumentValue):
            PlanChmf = PlanChmfPart(DocumentValue)
            return IsPartTarget(PlanChmf.StockValue.NameValue, TargetValue)
        if IsPatPart(DocumentValue):
            return CanWritePat(DocumentValue, TargetValue)
        if DocumentValue.brep is not None:
            _ = PlanImportPart(DocumentValue, TargetValue)
            return True
        PlanValue = PlanNativePart(DocumentValue)
    except (TypeError, ValueError):
        return False
    return IsPartTarget(PlanValue.NameValue, TargetValue)
