from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KAsmSuffix
from convert.adapters.solidworks.Core.Adapter import AsmDoc, RetainSource, SldprtAdapter
from convert.adapters.solidworks.Core.AssemblyReading.AsmReadData import AsmReadData
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdPart import (
    ReadColdPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# every input dependency for generated readback comes exclusively from the new model output
def ReadBundle(FilesValue: Mapping[FilePath, bytes], RootPath: FilePath) -> CadDocument:
    Index: dict[str, tuple[FilePath, ...]] = {
        PathValue.name.casefold(): (PathValue,) for PathValue in FilesValue
    }
    if len(Index) != len(FilesValue):
        raise ValueError("reopened bundle member locators collide")

    # linked archive reads must use only the computed container at the joined path
    def LoadArchive(PathValue: FilePath) -> SldprtArchive:
        return SldprtArchive.from_bytes(FilesValue[PathValue], str(PathValue))

    # both source kinds share the same logical names while avoiding filesystem resolution
    def LoadDocument(PathValue: FilePath, Settings: ReadOptions) -> CadDocument:
        Payload = FilesValue[PathValue]
        Label = str(PathValue)
        if PathValue.suffix.casefold() != KAsmSuffix:
            return ReadColdPart(Payload, Label, Settings)
        DocumentValue = AsmDoc(
            SldprtAdapter(),
            LoadArchive(PathValue),
            Payload,
            Label,
            Settings,
            Readback=AsmReadData(Index, LoadDocument, LoadArchive),
        )
        return RetainSource(DocumentValue, Payload)

    return LoadDocument(RootPath, ReadOptions())
