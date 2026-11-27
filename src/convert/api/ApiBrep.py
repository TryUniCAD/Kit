from __future__ import annotations

from pathlib import Path as FilePath

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.api.ApiContext import KConvertEngine
from convert.Geometry.BrepNames import MakeBrepNameMut
from convert.Geometry.BrepPayloads import GetBrepPayloads


# exact brep extraction gives callers native geometry bytes without invoking cad software
def ExtractBrep(
    SourceData: Source | CadDocument,
    FolderPath: str | FilePath,
    *,
    SourceFormat: str | None = None,
    Overwrite: bool = False,
) -> tuple[FilePath, ...]:
    DocumentData = (
        SourceData
        if isinstance(SourceData, CadDocument)
        else KConvertEngine.read(
            SourceData,
            format_id=SourceFormat,
            options=ReadOptions(
                include_brep=True,
                strict=True,
                extract_raw_brep=True,
            ),
        )
    )
    Payloads = GetBrepPayloads(DocumentData)
    if (
        not isinstance(SourceData, CadDocument)
        and DocumentData.source.format_id == KPartFormatId
        and not Payloads
    ):
        raise SldprtFormatError("SLDPRT contains no readable Parasolid payload")
    TargetPath = FilePath(FolderPath).expanduser().resolve()
    TargetPath.mkdir(parents=True, exist_ok=True)
    OutputPaths: list[FilePath] = []
    UsedNames: set[str] = set()
    for IndexValue, PayloadData in enumerate(Payloads, start=1):
        OutputName = MakeBrepNameMut(PayloadData, IndexValue, UsedNames)
        OutputPath = TargetPath / f"{OutputName}{PayloadData.FileExtension}"
        if OutputPath.exists() and not Overwrite:
            raise FileExistsError(OutputPath)
        PayloadBytes = PayloadData.PayloadData
        if PayloadBytes is None:
            continue
        _ = OutputPath.write_bytes(PayloadBytes)
        OutputPaths.append(OutputPath)
    return tuple(OutputPaths)
