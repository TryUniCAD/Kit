from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles


# bundle publication must use exactly the computed dependency members and retain their native ordering
def PublishNestMut(
    StagePath: FilePath,
    Candidates: tuple[tuple[PureWindowsPath, TargetDocument], ...],
    Profile: str,
) -> WriteResult:
    return WriteAsmFiles(
        StagePath,
        Candidates[-1][1].BytesValue,
        tuple(
            (PathValue.name, Value.BytesValue) for PathValue, Value in Candidates[:-1]
        ),
        Profile,
    )
