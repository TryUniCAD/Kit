from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeScopedThru import (
    MakeScopedThru,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import (
    MakeThroughPart,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ProjectThroughPart import (
    ProjectThroughPart,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability


# the internal through cut entry builds only from neutral feature intent the final locator and the supplied writer event
def PrepareThroughPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    CheckPlainScope(DocumentValue)
    CapabilityValues = KPartWriteCaps
    if DocumentValue.selections:
        CapabilityValues |= {Capability.KSelections}
    if not DocumentValue.capabilities <= CapabilityValues:
        raise ValueError("through-all preparation has unrepresented capabilities")
    Plan, Scope = ProjectThroughPart(DocumentValue)
    Config = DocumentValue.configurations[0]
    if Settings.configuration not in (None, Config.id, Config.name):
        raise ValueError("requested through-all write configuration is unavailable")
    Stock = Plan.StockValue
    Recipe = MakePartRecipe(Stock, WrittenAt)
    Output = FinalPartPath(TargetValue, Settings, Recipe.OutputValue, Stock.NameValue)
    Inputs = BindPartIntent(DocumentValue, Stock, Recipe, Output)
    CheckPartInput(DocumentValue, Inputs, Stock, (Plan.SketchName, Plan.FeatureName))
    if Scope is None:
        return MakeThroughPart(Plan, Inputs)
    return MakeScopedThru(Plan, Inputs, Scope).PartValue
