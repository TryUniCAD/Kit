from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupGeom import (
    CheckGroupGeom,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupNames import (
    CheckGroupNames,
)
from convert.adapters.solidworks.Archive.Construction.Perpendicular.CheckPerpGroup import (
    CheckPerpGroup,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWritePlan import (
    AsmWritePlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.MakeChildRecipe import (
    MakeChildRecipe,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadRectDisplay import (
    ReadRectDisplay,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmRules import (
    ReadAsmRules,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import (
    ReadAsmPaths,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import (
    ReadAsmPlace,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import (
    MakeNamedRecipe,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from interchange.document.Models.DocumentModel import CadDocument


# every portable domain must be admitted before constructor allocation can turn an incomplete intent into native output
def PlanAsmWrite(
    Document: CadDocument,
    NativePath: str,
    WrittenAt: int,
    *,
    ExactPlacements: Mapping[str, OccurrenceIn] | None = None,
) -> AsmWritePlan:
    ModelValue = ReadAsmModel(Document)
    RootPlanes = ReadAsmPlanes(Document)
    ChildPlanes = ReadAsmPlanes(ModelValue.ChildDocument)
    PathsValue = ReadAsmPaths(
        ModelValue.RootValue.name, ModelValue.ChildValue.name, NativePath, WrittenAt
    )
    ChildDocument = ReplaceValue(
        ModelValue.ChildDocument, support_planes=(ChildPlanes["z"],)
    )
    CheckPlainScope(ChildDocument)
    PlanValue = ProjectRectDims(ChildDocument)
    ChildRecipe = MakeChildRecipe(
        ChildDocument, PlanValue, ChildPlanes, PathsValue.ChildValue
    )
    Dimensions = ReadRectDisplay(PlanValue, ChildRecipe)
    RootRecipe = MakeNamedRecipe(
        ModelValue.RootValue.name,
        ModelValue.ConfigValue.name,
        ModelValue.GroupValue.name,
        ChildRecipe,
        RootPlanes,
        PathsValue.ParentValue,
    )
    Occurrences = tuple(
        ReadAsmPlace(Value) if ExactPlacements is None else ExactPlacements[Value.id]
        for Value in ModelValue.Occurrences
    )
    MateValues = ReadAsmRules(Document, ModelValue, ChildPlanes)
    CheckPerpGroup(Occurrences, MateValues)
    CheckGroupNames(RootRecipe, Occurrences, MateValues)
    for Value in MateValues:
        CheckGroupGeom(Occurrences, Value)
    return AsmWritePlan(
        ChildDocument,
        ChildRecipe,
        Dimensions,
        RootRecipe,
        Occurrences,
        MateValues,
        ModelValue.FixedIndex,
    )
