from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import (
    MakeRevPart,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.RevolvePart import (
    RevolvePart,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.RevPrepInput import (
    RevPrepInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# a scoped internal entry must construct a complete native revolve from the current document and explicit writer event without public registration
def PrepareRevolve(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> RevolvePart:
    InputValue = RevPrepInput(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    return MakeRevPart(DocumentValue, InputValue)
