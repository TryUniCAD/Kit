from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.ThruOwnerGraph import (
    ThruOwnerGraph,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph


# separate component results prevent partial owners from implying complete part output
@DataClass(frozen=True, slots=True)
class ThruConfigGraph:
    OwnersValue: ThruOwnerGraph
    DefinitionValue: ModelDefGraph
