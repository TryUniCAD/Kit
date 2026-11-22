from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipsePart import (
    BuildEllipPart,
    MakeEllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsColdEllip import IsColdEllip
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadColdEllip import (
    ReadColdEllip,
)
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
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
    IsReadback = IsColdEllip(DocumentValue)
    InputValue, PlanValue = (
        ReadColdEllip(DocumentValue)
        if IsReadback
        else (DocumentValue, PlanEllipse(DocumentValue))
    )
    (ConfigValue,) = DocumentValue.configurations
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested ellipse write configuration is unavailable")
    if type(CastValue(object, WrittenAt)) is not int or WrittenAt <= 0:
        raise ValueError("ellipse preparation requires positive integer creation time")
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    RecipeValue = ReplaceValue(RecipeValue, OutputValue=OutputValue)
    if not IsReadback:
        return MakeEllipsePart(InputValue, RecipeValue)
    CheckPartInput(InputValue, RecipeValue, PlanValue)
    Result = BuildEllipPart(PlanValue, RecipeValue)
    CheckColdRead(DocumentValue, Result.BytesValue, IsEllipse=True)
    return Result
