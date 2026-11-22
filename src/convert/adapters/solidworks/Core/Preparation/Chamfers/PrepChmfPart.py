from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Chamfers.EmitChmfPart import (
    EmitChmfPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfReadInput import (
    ChmfReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    PlanChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# native preparation keeps the measured part settings and actual final locator independent of output transport
def PrepChmfPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    IsReadback = IsColdRead(DocumentValue)
    InputValue = DocumentValue
    if IsReadback:
        FinalValue = Settings.values.get("final_destination", TargetValue)
        if not isinstance(FinalValue, (str, FilePath)):
            raise ValueError(
                "unnamed native streams require an explicit final destination"
            )
        InputValue = ChmfReadInput(DocumentValue, PureWindowsPath(FinalValue).stem)
    PlanValue = PlanChmfPart(InputValue)
    Config = InputValue.configurations[0]
    if Settings.configuration not in (None, Config.id, Config.name):
        raise ValueError("requested chamfer write configuration is unavailable")
    Stock = PlanValue.StockValue
    Recipe = MakePartRecipe(Stock, WrittenAt)
    Destination = FinalPartPath(
        TargetValue, Settings, Recipe.OutputValue, Stock.NameValue
    )
    NativePath = PureWindowsPath(Destination.PathName)
    if NativePath.drive.casefold() != "c:" or NativePath.stem != Stock.NameValue:
        raise ValueError(
            "chamfer destination requires a local C drive and the exact authored basename"
        )
    Candidate = EmitChmfPart(
        InputValue, PlanValue, ReplaceValue(Recipe, OutputValue=Destination)
    )
    if IsReadback:
        CheckColdRead(DocumentValue, Candidate.BytesValue)
    return Candidate
