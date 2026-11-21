from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmDef import (
    CheckAsmDef,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmOcc import (
    CheckAsmOcc,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmRoot import (
    CheckAsmRoot,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmConfig import (
    ReadAsmConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOrder import (
    ReadAsmOrder,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAssemblyPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedPartPlan import (
    NestedPartPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedLeaf import (
    ReadNestedLeaf,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import (
    ReadAsmPlace,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# one containing assembly owns the exact local pose order and explicit selected configuration of each direct child
def ReadNestedPlacements(
    Owner: ComponentDef,
    Occurrences: list[ComponentInst],
    Definitions: Mapping[str, ComponentDef],
) -> tuple[tuple[str, OccurrenceIn], ...]:
    Rows = tuple(sorted(Occurrences, key=ReadAsmOrder))
    RequireAsm(
        bool(Rows)
        and tuple(Value.order for Value in Rows) == tuple(range(len(Rows)))
        and len({Value.name for Value in Rows}) == len(Rows),
        "nested assembly requires a nonempty unambiguous local placement order",
    )
    for Value in Rows:
        Child = Definitions[Value.definition_id]
        CheckAsmOcc(
            Value,
            Owner,
            Child,
            Configuration(
                Child.configuration_id, Child.configuration_name, active=True
            ),
        )
        RequireAsm(
            not Value.fixed,
            "nested assembly requires the measured floating occurrences",
        )
    return tuple((Value.definition_id, ReadAsmPlace(Value)) for Value in Rows)


# validated acyclic definitions are emitted once after all their actual dependencies
def OrderNested(
    RootId: str,
    Definitions: Mapping[str, ComponentDef],
    Placements: Mapping[str, tuple[tuple[str, OccurrenceIn], ...]],
) -> tuple[ComponentDef, ...]:
    Chosen: dict[str, ComponentDef] = {}

    # separate visits retain the shared definition without flattening repeated occurrence paths
    def Visit(DefinitionId: str) -> None:
        if DefinitionId in Chosen:
            return
        for ChildId, _ in Placements.get(DefinitionId, ()):
            Visit(ChildId)
        Chosen[DefinitionId] = Definitions[DefinitionId]

    Visit(RootId)
    RequireAsm(
        set(Chosen) == set(Definitions),
        "nested assembly contains an unowned definition",
    )
    return tuple(Chosen.values())


# an ordinary rigid hierarchy must account for every definition document and placement before generating any files
def ReadNestedAssembly(Document: CadDocument) -> NestedAssemblyPlan:
    CheckAsmRoot(Document)
    Graph = Document.assembly
    if Graph is None:
        raise ValueError("nested assembly has no neutral definition graph")
    RequireAsm(
        not (
            Document.parameters
            or Graph.mates
            or Graph.mate_entities
            or Graph.mate_groups
            or Graph.attributes
        ),
        "nested assembly has unsupported mate or parameter state",
    )
    Definitions = {Value.id: Value for Value in Graph.definitions}
    Root = Definitions[Graph.root_definition_id]
    Config = ReadAsmConfig(Document)
    RequireAsm(
        Root.name == Document.metadata["name"]
        and (Root.configuration_name, Root.configuration_id) == (Config.name, Config.id)
        and len({Value.name.casefold() for Value in Definitions.values()})
        == len(Definitions),
        "nested root identity or relative filenames differ",
    )
    Embedded = {Value.id: Value.document for Value in Graph.documents}
    Parts: dict[str, NestedPartPlan] = {}
    EmbeddedUsed: set[str] = set()
    AssemblyOccurrences: dict[str, list[ComponentInst]] = {}
    for Value in Definitions.values():
        CheckAsmDef(Value)
        RequireAsm(
            bool(Value.configuration_id) and bool(Value.configuration_name),
            "nested definition needs an actual selected configuration",
        )
        if str(Value.kind) == "part":
            Child = Embedded.get(Value.document_id)
            if Child is None or Value.document_id in EmbeddedUsed:
                raise ValueError(
                    "nested definition does not own one distinct neutral part"
                )
            Parts[Value.id] = ReadNestedLeaf(Value, Child)
            EmbeddedUsed.add(Value.document_id)
        elif (
            str(Value.kind) == "assembly"
            and not Value.document_id
            and not Value.body_ids
        ):
            AssemblyOccurrences[Value.id] = []
        else:
            raise ValueError(
                "nested definition has unsupported kind or extra owned data"
            )
    RequireAsm(
        bool(Parts) and len(AssemblyOccurrences) >= 2 and EmbeddedUsed == set(Embedded),
        "nested assembly needs its complete owned part and subassembly inventory",
    )
    for Value in Graph.instances:
        AssemblyOccurrences[Value.owner_definition_id].append(Value)
    Placements = {
        Key: ReadNestedPlacements(Definitions[Key], Rows, Definitions)
        for Key, Rows in AssemblyOccurrences.items()
    }
    Planes = ReadAsmPlanes(Document)
    return NestedAssemblyPlan(
        Root, OrderNested(Root.id, Definitions, Placements), Planes, Parts, Placements
    )
