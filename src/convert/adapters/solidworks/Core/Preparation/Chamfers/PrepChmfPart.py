from dataclasses import replace as ReplaceValue
from pathlib import PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Chamfers.EmitChmfPart import (
    EmitChmfPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    PlanChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# native preparation keeps the measured part settings and actual final locator independent of output transport
def PrepChmfPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    PlanValue = PlanChmfPart(DocumentValue)
    Config = DocumentValue.configurations[0]
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
    return EmitChmfPart(
        DocumentValue, PlanValue, ReplaceValue(Recipe, OutputValue=Destination)
    )
