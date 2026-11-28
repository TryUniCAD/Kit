from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)


# full definition readback needs its actual map and consumed grammar rather than a concept prefix alone
@DataClass(frozen=True, slots=True)
class DefinitionRead:
    GraphValue: BlankGraph
    MapValue: MapSnapshot
    UsageValue: BodyUsage
