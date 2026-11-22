from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipsePart import (
    MakeEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Ellipse.PlanEllipse import PlanEllipse
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# ordinary ellipse preparation needs the actual selected configuration final locator and one authored creation event
def PrepareEllipse(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> EllipsePart:
    SettingsValue = CheckPartOpts(OptionsValue)
    PlanValue = PlanEllipse(DocumentValue)
    (ConfigValue,) = DocumentValue.configurations
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested ellipse write configuration is unavailable")
    if type(CastValue(object, WrittenAt)) is not int or WrittenAt <= 0:
        raise ValueError("ellipse preparation requires positive integer creation time")
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    return MakeEllipsePart(
        DocumentValue, ReplaceValue(RecipeValue, OutputValue=OutputValue)
    )
