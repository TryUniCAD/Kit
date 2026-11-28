from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.BuildChmfPart import (
    BuildChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.CheckChmfRead import (
    CheckChmfRead,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# native destination preparation still requires the complete original readback to match exact regeneration
def PrepChmfPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    Candidate = BuildChmfPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsColdRead(DocumentValue):
        CheckChmfRead(DocumentValue, Candidate.BytesValue)
    return Candidate
