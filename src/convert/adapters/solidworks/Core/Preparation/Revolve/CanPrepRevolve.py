from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.Revolve.RevPrepInput import (
    RevPrepInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# internal callers need the same complete neutral options and pathname admission without enabling an unqualified public writer
def CanPrepRevolve(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> bool:
    try:
        _ = RevPrepInput(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    except (TypeError, ValueError, KeyError):
        return False
    return True
