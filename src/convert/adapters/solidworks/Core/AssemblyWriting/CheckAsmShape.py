from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupGeom import (
    CheckGroupGeom,
)
from convert.adapters.solidworks.Archive.Construction.Perpendicular.CheckPerpGroup import (
    CheckPerpGroup,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmRules import (
    ReadAsmRules,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import (
    ReadAsmPlace,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.CheckWriteMates import (
    CheckWriteMates,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from interchange.document.Models.DocumentModel import CadDocument


# writer selection must validate neutral ownership geometry and parameters before any path mapping or staging exists
def CheckAsmShape(DocumentValue: CadDocument) -> str:
    ModelValue = ReadAsmModel(DocumentValue)
    _ = ReadAsmPlanes(DocumentValue)
    PlaneValues = ReadAsmPlanes(ModelValue.ChildDocument)
    ChildValue = ReplaceValue(
        ModelValue.ChildDocument, support_planes=(PlaneValues["z"],)
    )
    CheckPlainScope(ChildValue)
    PlanValue = ProjectRectDims(ChildValue)
    if (PlanValue.SketchDriverNames, PlanValue.DepthName) != (("D1", "D2"), "D1"):
        raise ValueError(
            "public assembly writing requires its qualified child driver names"
        )
    Placements = tuple(ReadAsmPlace(Value) for Value in ModelValue.Occurrences)
    MateValues = ReadAsmRules(DocumentValue, ModelValue, PlaneValues)
    CheckWriteMates(Placements, MateValues)
    CheckPerpGroup(Placements, MateValues)
    for MateValue in MateValues:
        CheckGroupGeom(Placements, MateValue)
    return ModelValue.RootValue.name
