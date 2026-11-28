from collections.abc import Mapping

from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmDef import (
    CheckAsmDef,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedPartPlan import (
    NestedPartPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedLeaf import (
    ReadNestedLeaf,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import AssemblyData


# each nested definition owns one distinct part document or one assembly placement list
def ReadNestMembers(
    GraphValue: AssemblyData, Definitions: Mapping[str, ComponentDef]
) -> tuple[dict[str, NestedPartPlan], dict[str, list[ComponentInst]]]:
    Embedded = {Value.id: Value.document for Value in GraphValue.documents}
    Parts: dict[str, NestedPartPlan] = {}
    EmbeddedUsed: set[str] = set()
    AssemblyOccurrences: dict[str, list[ComponentInst]] = {}
    for Definition in Definitions.values():
        CheckAsmDef(Definition)
        RequireAsm(
            bool(Definition.configuration_id) and bool(Definition.configuration_name),
            "nested definition needs an actual selected configuration",
        )
        if str(Definition.kind) == "part":
            Child = Embedded.get(Definition.document_id)
            if Child is None or Definition.document_id in EmbeddedUsed:
                raise ValueError(
                    "nested definition does not own one distinct neutral part"
                )
            Parts[Definition.id] = ReadNestedLeaf(Definition, Child)
            EmbeddedUsed.add(Definition.document_id)
        elif (
            str(Definition.kind) == "assembly"
            and not Definition.document_id
            and not Definition.body_ids
        ):
            AssemblyOccurrences[Definition.id] = []
        else:
            raise ValueError(
                "nested definition has unsupported kind or extra owned data"
            )
    RequireAsm(
        bool(Parts) and len(AssemblyOccurrences) >= 2 and EmbeddedUsed == set(Embedded),
        "nested assembly needs its complete owned part and subassembly inventory",
    )
    for Occurrence in GraphValue.instances:
        AssemblyOccurrences[Occurrence.owner_definition_id].append(Occurrence)
    return Parts, AssemblyOccurrences
