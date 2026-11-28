from pathlib import PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Shells.EmitShellPart import (
    EmitShellPart,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Shells.PlanOpenShell import (
    PlanOpenShell,
)
from interchange.document.Models.DocumentModel import CadDocument


# the constructor encodes the actual standalone shell locator while keeping the returned artifact in memory
def BuildShellPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    Options = CheckPartOpts(OptionsValue)
    PlanValue = PlanOpenShell(DocumentValue)
    Config = DocumentValue.configurations[0]
    if Options.configuration not in (None, Config.id, Config.name):
        raise ValueError("requested shell write configuration is unavailable")
    Stock = PlanValue.StockValue
    Recipe = MakePartRecipe(Stock, WrittenAt)
    Output = FinalPartPath(TargetValue, Options, Recipe.OutputValue, Stock.NameValue)
    if PureWindowsPath(Output.PathName).stem != Stock.NameValue:
        raise ValueError("shell destination requires the exact authored basename")
    return EmitShellPart(
        DocumentValue, PlanValue, BindPartIntent(DocumentValue, Stock, Recipe, Output)
    )
