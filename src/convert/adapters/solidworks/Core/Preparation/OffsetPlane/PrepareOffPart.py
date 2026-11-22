from dataclasses import replace as ReplaceValue
from pathlib import PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffPart import (
    MakeOffPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReadRingPoint import (
    ReadRingPoint,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.IsOffRead import IsOffRead
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PlanOffPart import (
    PlanOffPart,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PlanOffRead import (
    PlanOffRead,
)
from interchange.document.Models.DocumentModel import CadDocument


# neutral offset preparation uses the ordinary sdk settings and a deterministic caller owned locator and epoch
def PrepareOffPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
    *,
    RecipeValue: PartBuildInput | None = None,
    TextPoint: tuple[float, float] | None = None,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    PlanValue, DatumValue = (
        PlanOffRead(
            DocumentValue, PureWindowsPath(RecipeValue.OutputValue.PathName).stem
        )
        if RecipeValue is not None and IsOffRead(DocumentValue)
        else PlanOffPart(DocumentValue)
    )
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested offset write configuration is unavailable")
    if TextPoint is not None:
        PlanValue = ReplaceValue(PlanValue, TextPoint=ReadRingPoint(TextPoint))
    if RecipeValue is None:
        RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    elif any(
        Value != WrittenAt
        for Value in (
            RecipeValue.HeaderValue.CreatedAt,
            RecipeValue.HistoryValue.CreatedAt,
            RecipeValue.SystemValue.CreatedAt,
        )
    ):
        raise ValueError(
            "offset part creation epochs must agree with the authored event"
        )
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    if PureWindowsPath(OutputValue.PathName).stem != PlanValue.NameValue:
        raise ValueError("offset output must retain the exact modeled basename")
    InputValue = BindPartIntent(DocumentValue, PlanValue, RecipeValue, OutputValue)
    return MakeOffPart(
        PlanValue,
        DatumValue,
        ReplaceValue(
            InputValue,
            SystemValue=ReplaceValue(
                InputValue.SystemValue, OriginAxis=PlanValue.AxisValue
            ),
        ),
    )
