from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import (
    PlanRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevInput import (
    ReadRevInput,
)
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.document.Models.DocumentModel import CadDocument


# readback preflight binds the selected datum and driver before the registry stages output
def CanWriteRev(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    PathValue = FilePath(TargetValue) if isinstance(TargetValue, (str, FilePath)) else None
    NameValue = PathValue.stem if PathValue is not None else DocumentValue.sketches[0].name
    PlanValue = PlanRevolve(ReadRevInput(DocumentValue, NameValue))
    return PlanValue is not None and IsPartTarget(PlanValue.NameValue, TargetValue)
