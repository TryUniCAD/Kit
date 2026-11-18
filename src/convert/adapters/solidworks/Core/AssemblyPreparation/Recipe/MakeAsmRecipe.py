from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.AsmSavePolicy import (
    KAsmSavePolicy,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.DefaultAsmTree import (
    DefaultAsmTree,
)
from interchange.geometry.Models.SupportPlane import SupportPlane


# shared native metadata must use one construction event while assembly identity remains separate from its actual child
def MakeAsmRecipe(
    ModelValue: AsmRootData,
    ChildRecipe: PartBuildInput,
    PlanesValue: Mapping[str, SupportPlane],
    NativeSelf: SelfFileInput,
) -> AssemblyInput:
    SystemValue = DefaultAsmTree(
        ChildRecipe, PlanesValue, ModelValue.GroupValue.name, NativeSelf.SavedAt
    )
    return AssemblyInput(
        ModelValue.RootValue.name,
        ModelValue.ConfigValue.name,
        ChildRecipe.ManagerName,
        ChildRecipe.StyleValue,
        ChildRecipe.DocumentUnits,
        SystemValue,
        ChildRecipe.TargetValue,
        ChildRecipe.HeaderValue,
        ChildRecipe.HistoryValue,
        ChildRecipe.DefinitionValue,
        NativeSelf,
        KAsmSavePolicy,
    )
