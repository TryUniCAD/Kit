from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadEllipInput import (
    ReadEllipInput,
)
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.document.Models.DocumentModel import CadDocument


# source selection validates exact conic and live boss ownership before normal staging
def CanWriteEllip(Document: CadDocument, Target: KTargetType) -> bool:
    PathValue = FilePath(Target) if isinstance(Target, (str, FilePath)) else None
    NameValue = (
        PureWindowsPath(PathValue).stem
        if PathValue is not None
        else Document.sketches[0].name
    )
    _, PlanValue = ReadEllipInput(Document, NameValue)
    return IsPartTarget(PlanValue.NameValue, Target) and (
        PathValue is None or not PathValue.is_dir()
    )
