from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepNestedPlan import (
    PrepNestedPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAsm,
)
from interchange.document.Models.DocumentModel import CadDocument


# clean authored input keeps the existing neutral nested preparation entry
def PrepNestedAsm(
    Document: CadDocument, NativePath: str, WrittenAt: int
) -> tuple[tuple[PureWindowsPath, TargetDocument], ...]:
    return PrepNestedPlan(ReadNestedAsm(Document), NativePath, WrittenAt)
