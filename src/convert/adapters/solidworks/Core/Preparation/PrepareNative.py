from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.RevolvePart import (
    RevolvePart,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.MakeSelectedRevolvePart import (
    MakeSelectedRevolvePart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import (
    PrepareCircle,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import (
    PrepareEqPart,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanTopCorner import (
    PlanTopCorner,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import (
    PrepareImport,
)
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockChain
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.Patterns.PatCandidate import (
    PatCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import (
    PrepPatPart,
)
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import (
    PlanPublicRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanSelectedRevolve import (
    PlanSelectedRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinPart import (
    PlanThinPart,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.RevPrepInput import (
    RevPrepInput,
)
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
    PrepareStockPart,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockCandidate import (
    StockCandidate,
)
from interchange.document.Models.DocumentModel import CadDocument


# native part preparation must construct its only recipe from the neutral model target policy and one writer event before output is touched
def PrepareNative(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate | ImportCandidate | StockCandidate | RevolvePart | PatCandidate:
    if IsPatPart(DocumentValue):
        return PrepPatPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if PlanThinPart(DocumentValue) is not None:
        return PrepareRevolve(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if DocumentValue.brep is not None:
        return PrepareImport(
            DocumentValue, TargetValue, WrittenAt, CheckPartOpts(OptionsValue)
        )
    if any(Parameter.expression is not None for Parameter in DocumentValue.parameters):
        return PrepareEqPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsStockChain(DocumentValue):
        return PrepareStockPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    SettingsValue = CheckPartOpts(OptionsValue)
    SelectedValue = PlanSelectedRevolve(DocumentValue)
    if SelectedValue is not None:
        Recipe = RevPrepInput(
            DocumentValue,
            TargetValue,
            WrittenAt,
            SettingsValue,
            PlanValue=SelectedValue.OperationsValue[0],
        )
        return MakeSelectedRevolvePart(DocumentValue, Recipe)
    if PlanPublicRevolve(DocumentValue) is not None:
        return PrepareRevolve(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    TopValue = PlanTopCorner(DocumentValue)
    if TopValue is not None:
        Projected, TopPlan = TopValue
        return RunPartPrep(
            Projected,
            TargetValue,
            TopPlan,
            MakePartRecipe(TopPlan, WrittenAt),
            SettingsValue,
            TopCorner=True,
        )
    try:
        PlanValue = PlanPartWrite(DocumentValue)
    except (TypeError, ValueError):
        return PrepareCircle(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    return RunPartPrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
