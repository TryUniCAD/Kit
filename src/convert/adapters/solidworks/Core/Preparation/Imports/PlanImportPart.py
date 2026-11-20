from ntpath import splitdrive as SplitDrive
from os import fspath as PathText
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Archive.Construction.Part.Imports.CheckBareImport import (
    ReadBareModel,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadBareConfig import (
    ReadBareConfig,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.ReadCylShape import (
    ReadCylShape,
)
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.Imports.ImportPartPlan import (
    ImportPartPlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# selection and emission need the same geometry and source guards before any destination can be published
def PlanImportPart(
    DocumentValue: CadDocument, TargetValue: KTargetType
) -> ImportPartPlan:
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("native periodic import requires a part path")
    TargetText = PathText(TargetValue)
    PathValue = (
        PureWindowsPath(TargetText)
        if SplitDrive(TargetText)[0]
        else FilePath(TargetText)
    )
    if PathValue.suffix.casefold() != KPartSuffix:
        raise ValueError("native periodic import requires an SLDPRT destination")
    ModelValue = ReadBareModel(DocumentValue)
    ConfigValue = ReadBareConfig(DocumentValue)
    SourceValue = DocumentValue.source
    if (
        SourceValue.path != ""
        or SourceValue.sha256 != ""
        or SourceValue.container_version != ""
        or SourceValue.application_version != ""
    ):
        raise ValueError("native periodic import cannot preserve source file identity")
    if any(
        type(NameValue) is not str
        or not NameValue.strip()
        or not NameValue.isprintable()
        for NameValue in (PathValue.stem, ConfigValue.name)
    ):
        raise ValueError("native periodic import requires printable names")
    _ = ReadCylShape(ModelValue)
    return ImportPartPlan(PathValue.stem, ConfigValue.name)
