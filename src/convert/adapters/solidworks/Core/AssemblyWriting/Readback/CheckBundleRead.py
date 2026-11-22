from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadBundle import (
    ReadBundle,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# candidate bytes must reconstruct every original reader field before publication can begin
def CheckBundleRead(
    Document: CadDocument,
    Candidates: tuple[tuple[PureWindowsPath, bytes], ...],
    *,
    ScopeValue: str = "nested",
) -> None:
    GraphValue = Document.assembly
    if GraphValue is None:
        raise ValueError("reopened bundle lacks its source definition graph")
    RootPath = next(
        (
            FilePath(Value.source_path)
            for Value in GraphValue.definitions
            if Value.id == GraphValue.root_definition_id
        ),
        None,
    )
    SourcePaths = {FilePath(Value.source_path) for Value in GraphValue.definitions}
    NamesValue = {Value.name.casefold(): Value for Value in SourcePaths}
    FilesValue = {
        PathValue.name.casefold(): Payload for PathValue, Payload in Candidates
    }
    if (
        RootPath is None
        or len(SourcePaths) != len(NamesValue)
        or len(Candidates) != len(FilesValue)
        or NamesValue.keys() != FilesValue.keys()
    ):
        raise ValueError(
            "reopened bundle source members differ from their regenerated members"
        )
    Expected = ReadBundle(
        {Value: FilesValue[NameValue] for NameValue, Value in NamesValue.items()},
        RootPath,
        RootLabel=Document.source.path,
    )
    if ToJson(Document, IndentSize=None) != ToJson(Expected, IndentSize=None):
        raise ValueError(
            f"SOLIDWORKS {ScopeValue} readback differs from its regenerated bundle"
        )
