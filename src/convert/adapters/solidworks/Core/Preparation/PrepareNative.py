from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
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
    MakeSelRevPart,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsChmfPart import IsChmfPart
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import (
    PrepChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipsePart import (
    IsEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import (
    PrepareEllipse,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import (
    PrepareEqPart,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import (
    PrepareImport,
)
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockChain
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.Patterns.PatCandidate import (
    PatCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import (
    PrepPatPart,
)
from convert.adapters.solidworks.Core.Preparation.PrepPlainPart import PrepPlainPart
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import (
    PlanRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanSelectedRevolve import (
    PlanSelRevolve,
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
from convert.adapters.solidworks.Core.Preparation.Readback.PrepareColdPart import (
    PrepareColdPart,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.Sweeps.IsSweepPart import IsSweepPart
from convert.adapters.solidworks.Core.Preparation.Sweeps.PrepSweepPart import (
    PrepSweepPart,
)
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
) -> (
    PartCandidate
    | ImportCandidate
    | StockCandidate
    | RevolvePart
    | PatCandidate
    | EllipsePart
    | SweepPart
):
    if IsColdRead(DocumentValue):
        return PrepareColdPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsSweepPart(DocumentValue):
        return PrepSweepPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsChmfPart(DocumentValue):
        return PrepChmfPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsPatPart(DocumentValue):
        return PrepPatPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    if IsEllipsePart(DocumentValue):
        return PrepareEllipse(DocumentValue, TargetValue, WrittenAt, OptionsValue)
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
    SelectedValue = PlanSelRevolve(DocumentValue)
    if SelectedValue is not None:
        Recipe = RevPrepInput(
            DocumentValue,
            TargetValue,
            WrittenAt,
            SettingsValue,
            PlanValue=SelectedValue.OperationsValue[0],
        )
        return MakeSelRevPart(DocumentValue, Recipe)
    if PlanRevolve(DocumentValue) is not None:
        return PrepareRevolve(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    return PrepPlainPart(DocumentValue, TargetValue, WrittenAt, SettingsValue)
