from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.CylChild import (
    CylChild,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.MakeCylChild import (
    MakeCylChild,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# assembly preparation must bind its actual child locator and authored scene before building the part
def PrepCylChild(
    DocumentValue: CadDocument,
    OutputValue: SelfFileInput,
    SceneName: str,
    LightValues: tuple[LightInput, ...],
) -> CylChild:
    if not ReadStyleText(SceneName, "concentric child environment"):
        raise ValueError("concentric child requires an authored environment name")
    PlanValue = PlanCircle(DocumentValue, Measured=True)
    RecipeValue = MakePartRecipe(PlanValue, OutputValue.SavedAt)
    SystemValue = RecipeValue.SystemValue
    FoldersValue = tuple(
        (ClassName, SceneName if ClassName == "moEnvFolder_c" else NameValue)
        for ClassName, NameValue in SystemValue.FolderValues
    )
    RecipeValue = ReplaceValue(
        RecipeValue, SystemValue=ReplaceValue(SystemValue, FolderValues=FoldersValue)
    )
    InputValue = BindPartIntent(DocumentValue, PlanValue, RecipeValue, OutputValue)
    return MakeCylChild(DocumentValue, InputValue, LightValues)
