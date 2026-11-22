from dataclasses import replace as ReplaceValue
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import (
    MakePartTarget,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetAudit import (
    TargetAudit,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakeNestedAsm import (
    MakeNestedAsm,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import (
    MakeRectDimPart,
)
from convert.adapters.solidworks.Container.Format import KAsmSuffix, KPartSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadRectDisplay import (
    ReadRectDisplay,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.CheckNativePath import (
    CheckNativePath,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import (
    MakeNamedRecipe,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe


# construction keeps one generated native model per definition and assigns only caller owned sibling destinations
def PrepNestedPlan(
    PlanValue: NestedAsmPlan, NativePath: str, WrittenAt: int
) -> tuple[tuple[PureWindowsPath, TargetDocument], ...]:
    ParentPath = CheckNativePath(NativePath)
    RequireAsm(
        ParentPath.stem == PlanValue.RootValue.name
        and ParentPath.suffix.casefold() == KAsmSuffix,
        "nested assembly destination must retain the modeled root basename",
    )
    DefaultRecipe = MakePartRecipe(
        next(iter(PlanValue.LeafValues.values())).PartValue, WrittenAt
    )
    Targets: dict[str, TargetDocument] = {}
    Results: list[tuple[PureWindowsPath, TargetDocument]] = []
    AuditValue = TargetAudit()
    for Definition in PlanValue.OrderedDefinitions:
        LeafValue = PlanValue.LeafValues.get(Definition.id)
        FileName = (
            Definition.name + (KAsmSuffix if LeafValue is None else KPartSuffix).upper()
        )
        Native = (
            ParentPath
            if Definition is PlanValue.RootValue
            else CheckNativePath(str(ParentPath.parent / FileName))
        )
        RequireAsm(
            Native.parent == ParentPath.parent
            and Native.name.casefold() == FileName.casefold(),
            "nested definition destination must be a distinct sibling filename",
        )
        SelfFile = SelfFileInput(str(Native), WrittenAt, IsAssembly=LeafValue is None)
        if LeafValue is None:
            Recipe = MakeNamedRecipe(
                Definition.name,
                Definition.configuration_name,
                "Mates",
                DefaultRecipe,
                PlanValue.PlanesValue,
                SelfFile,
            )
            Placements = tuple(
                TargetPlacement(Targets[IdValue], Value)
                for IdValue, Value in PlanValue.PlacementsValue[Definition.id]
            )
            Value = MakeNestedAsm(Recipe, Placements, AuditValue)
        else:
            PartRecipe = ReplaceValue(
                MakePartRecipe(LeafValue.PartValue, WrittenAt), OutputValue=SelfFile
            )
            if len(LeafValue.DocumentValue.parameters) == 3:
                Dimensions = ReadRectDisplay(LeafValue.PartValue, PartRecipe)
                PartValue = MakeRectDimPart(
                    LeafValue.DocumentValue, PartRecipe, Dimensions
                )
            else:
                PartValue = MakeBlindPart(LeafValue.DocumentValue, PartRecipe)
            Value = MakePartTarget(PartValue)
        Targets[Definition.id] = Value
        Results.append((Native, Value))
    return tuple(Results)
