from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupGeom import (
    CheckGroupGeom,
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
    _ = ProjectRectDims(ChildValue)
    Placements = tuple(ReadAsmPlace(Value) for Value in ModelValue.Occurrences)
    MateValues = ReadAsmRules(DocumentValue, ModelValue, PlaneValues)
    for MateValue in MateValues:
        CheckGroupGeom(Placements, MateValue)
    return ModelValue.RootValue.name
