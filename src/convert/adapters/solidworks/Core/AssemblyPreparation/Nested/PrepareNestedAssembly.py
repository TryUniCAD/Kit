from dataclasses import replace as ReplaceValue
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import (
    MakePartTarget,
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
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadRectDisplay import (
    ReadRectDisplay,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAssembly,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.CheckNativePath import (
    CheckNativePath,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import (
    MakeNamedAsmRecipe,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# construction keeps one generated native model per definition and assigns only caller owned sibling destinations
def PrepareNestedAssembly(
    Document: CadDocument, NativePath: str, WrittenAt: int
) -> tuple[tuple[PureWindowsPath, TargetDocument], ...]:
    Plan = ReadNestedAssembly(Document)
    ParentPath = CheckNativePath(NativePath)
    RequireAsm(
        ParentPath.stem == Plan.RootValue.name
        and ParentPath.suffix.casefold() == ".sldasm",
        "nested assembly destination must retain the modeled root basename",
    )
    DefaultRecipe = MakePartRecipe(
        next(iter(Plan.LeafValues.values())).PartValue, WrittenAt
    )
    Targets: dict[str, TargetDocument] = {}
    Results: list[tuple[PureWindowsPath, TargetDocument]] = []
    for Definition in Plan.OrderedDefinitions:
        Leaf = Plan.LeafValues.get(Definition.id)
        Name = Definition.name + (".SLDASM" if Leaf is None else ".SLDPRT")
        Native = (
            ParentPath
            if Definition is Plan.RootValue
            else CheckNativePath(str(ParentPath.parent / Name))
        )
        RequireAsm(
            Native.parent == ParentPath.parent
            and Native.name.casefold() == Name.casefold(),
            "nested definition destination must be a distinct sibling filename",
        )
        SelfFile = SelfFileInput(str(Native), WrittenAt)
        if Leaf is None:
            Recipe = MakeNamedAsmRecipe(
                Definition.name,
                Definition.configuration_name,
                "Mates",
                DefaultRecipe,
                Plan.PlanesValue,
                SelfFile,
            )
            Placements = tuple(
                TargetPlacement(Targets[IdValue], Value)
                for IdValue, Value in Plan.PlacementsValue[Definition.id]
            )
            Value = MakeNestedAsm(Recipe, Placements)
        else:
            PartRecipe = ReplaceValue(
                MakePartRecipe(Leaf.PartValue, WrittenAt), OutputValue=SelfFile
            )
            if len(Leaf.DocumentValue.parameters) == 3:
                Dimensions = ReadRectDisplay(Leaf.PartValue, PartRecipe)
                Part = MakeRectDimPart(Leaf.DocumentValue, PartRecipe, Dimensions)
            else:
                Part = MakeBlindPart(Leaf.DocumentValue, PartRecipe)
            Value = MakePartTarget(Part)
        Targets[Definition.id] = Value
        Results.append((Native, Value))
    return tuple(Results)
