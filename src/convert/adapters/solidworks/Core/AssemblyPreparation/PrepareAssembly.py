from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import (
    MakePlanarGroup,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import (
    MakeRectDimPart,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import (
    PlanAsmWrite,
)
from interchange.document.Models.DocumentModel import CadDocument


# complete assembly output must reuse the original generated child objects and common ordered mate constructors without any replay source
def PrepareAssembly(
    Document: CadDocument, NativePath: str, WrittenAt: int
) -> OrderedAsm:
    PlanValue = PlanAsmWrite(Document, NativePath, WrittenAt)
    ChildValue = MakeRectDimPart(
        PlanValue.ChildDocument, PlanValue.ChildRecipe, PlanValue.ChildDimensions
    )
    return MakePlanarGroup(
        ChildValue,
        PlanValue.RootRecipe,
        PlanValue.Occurrences,
        PlanValue.MatesValue,
        PlanValue.FixedIndex,
    )
