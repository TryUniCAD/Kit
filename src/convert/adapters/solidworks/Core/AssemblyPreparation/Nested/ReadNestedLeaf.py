from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmConfig import (
    ReadAsmConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedPartPlan import (
    NestedPartPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.document.Models.DocumentModel import CadDocument


# a reusable leaf must be the actual owned neutral rectangular boss with its active configuration
def ReadNestedLeaf(Definition: ComponentDef, Document: CadDocument) -> NestedPartPlan:
    Config = ReadAsmConfig(Document)
    RequireAsm(
        Document.assembly is None
        and Definition.name == Document.metadata.get("name")
        and Definition.body_ids == tuple(Value.id for Value in Document.bodies)
        and (Definition.configuration_name, Definition.configuration_id)
        == (Config.name, Config.id),
        "nested leaf differs from its actual part or configuration",
    )
    if len(Document.parameters) == 3:
        CheckPlainScope(Document)
        RequireAsm(
            Document.units == "mm" and Document.capabilities <= KPartWriteCaps,
            "dimensioned nested leaf requires the ordinary millimetre part domains",
        )
        Plan = ProjectRectDims(Document)
    else:
        Plan = PlanPartWrite(Document)
    Vertices = Plan.VerticesValue
    XValues = {X for X, _ in Vertices}
    YValues = {Y for _, Y in Vertices}
    RequireAsm(
        len(Vertices) == 4
        and len(XValues) == len(YValues) == 2
        and set(Vertices) == {(X, Y) for X in XValues for Y in YValues}
        and Plan.PlaneName == "Front Plane"
        and Plan.DepthName == "D1",
        "nested leaf requires its ordinary rectangular blind depth",
    )
    return NestedPartPlan(Document, Plan)
