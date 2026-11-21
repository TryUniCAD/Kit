from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedPartPlan import (
    NestedPartPlan,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.geometry.Models.SupportPlane import SupportPlane


# the neutral plan keeps local placements separate for each reusable definition in dependency order
@Dataclass(frozen=True, slots=True)
class NestedAssemblyPlan:
    RootValue: ComponentDef
    OrderedDefinitions: tuple[ComponentDef, ...]
    PlanesValue: Mapping[str, SupportPlane]
    LeafValues: Mapping[str, NestedPartPlan]
    PlacementsValue: Mapping[str, tuple[tuple[str, OccurrenceIn], ...]]
