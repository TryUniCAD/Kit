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
        PlanValue = ProjectRectDims(Document)
    else:
        PlanValue = PlanPartWrite(Document)
    Vertices = PlanValue.VerticesValue
    XValues = {XValue for XValue, _ in Vertices}
    YValues = {YValue for _, YValue in Vertices}
    RequireAsm(
        len(Vertices) == 4
        and len(XValues) == len(YValues) == 2
        and set(Vertices)
        == {(XValue, YValue) for XValue in XValues for YValue in YValues}
        and PlanValue.PlaneName == "Front Plane"
        and PlanValue.DepthName == "D1",
        "nested leaf requires its ordinary rectangular blind depth",
    )
    return NestedPartPlan(Document, PlanValue)
