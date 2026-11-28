from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import (
    ComposeEllipse,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadEllipInput import (
    ReadEllipInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from interchange.document.Models.DocumentModel import CadDocument


# a fresh constructor replaces the source carrier only after complete strict ellipse comparison
def PrepEllipRead(
    Document: CadDocument,
    Target: KTargetType,
    WrittenAt: int,
    Options: WriteOptions | None,
) -> EllipsePart:
    Settings = CheckPartOpts(Options)
    FinalValue = Settings.values.get("final_destination", Target)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError("unnamed native streams require an explicit final destination")
    InputValue, PlanValue = ReadEllipInput(Document, PureWindowsPath(FinalValue).stem)
    Candidate = ComposeEllipse(InputValue, PlanValue, Target, WrittenAt, Settings)
    CheckColdRead(Document, Candidate.BytesValue, IncludeBrep=Document.brep is not None)
    return Candidate
