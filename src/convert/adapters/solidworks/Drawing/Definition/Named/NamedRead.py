from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph


# named readback must retain the selected family alongside the actual archive map and usage evidence
@DataClass(frozen=True, slots=True)
class NamedRead:
    GraphValue: NamedGraph
    MapValue: MapSnapshot
    UsageValue: BodyUsage
