from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepTopPart import (
    PrepTopPart,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.ReadTopInput import (
    ReadTopInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from interchange.document.Models.DocumentModel import CadDocument


# anchored top readback regenerates the shared part and verifies every retained source field before returning a candidate
def PrepColdTop(
    Document: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None,
    *,
    PlatformMath: bool = False,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    FinalValue = Settings.values.get("final_destination", TargetValue)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError(
            "unnamed Top corner streams require an explicit final destination"
        )
    NeutralValue = ReadTopInput(Document, PureWindowsPath(FinalValue).stem)
    Candidate = PrepTopPart(
        NeutralValue, TargetValue, WrittenAt, Settings, PlatformMath=PlatformMath
    )
    CheckColdRead(Document, Candidate.BytesValue)
    return Candidate
