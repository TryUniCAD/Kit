from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
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
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestMembers import (
    ReadNestMembers,
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
def ReadNestPlaces(
    Owner: ComponentDef,
    Occurrences: list[ComponentInst],
    Definitions: Mapping[str, ComponentDef],
    ExactPlacements: Mapping[str, OccurrenceIn] | None = None,
) -> tuple[tuple[str, OccurrenceIn], ...]:
    SortedRows = tuple(sorted(Occurrences, key=ReadAsmOrder))
    RequireAsm(
        bool(SortedRows)
        and tuple(Value.order for Value in SortedRows) == tuple(range(len(SortedRows)))
        and len({Value.name for Value in SortedRows}) == len(SortedRows),
        "nested assembly requires a nonempty unambiguous local placement order",
    )
    for Value in SortedRows:
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
    return tuple(
        (
            Value.definition_id,
            (
                ReadAsmPlace(Value)
                if ExactPlacements is None
                else ExactPlacements[Value.id]
            ),
        )
        for Value in SortedRows
    )


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
def ReadNestedAsm(
    Document: CadDocument, *, ExactPlacements: Mapping[str, OccurrenceIn] | None = None
) -> NestedAsmPlan:
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
    RootValue = Definitions[Graph.root_definition_id]
    Config = ReadAsmConfig(Document)
    RequireAsm(
        RootValue.name == Document.metadata["name"]
        and (RootValue.configuration_name, RootValue.configuration_id)
        == (Config.name, Config.id)
        and len({(Value.kind, Value.name.casefold()) for Value in Definitions.values()})
        == len(Definitions),
        "nested root identity or relative filenames differ",
    )
    Parts, AssemblyOccurrences = ReadNestMembers(Graph, Definitions)
    Placements = {
        OwnerId: ReadNestPlaces(
            Definitions[OwnerId], OccurrenceRows, Definitions, ExactPlacements
        )
        for OwnerId, OccurrenceRows in AssemblyOccurrences.items()
    }
    Planes = ReadAsmPlanes(Document)
    return NestedAsmPlan(
        RootValue,
        OrderNested(RootValue.id, Definitions, Placements),
        Planes,
        Parts,
        Placements,
    )
