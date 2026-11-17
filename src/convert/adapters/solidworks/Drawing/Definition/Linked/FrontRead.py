from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph


# complete readback must carry its actual linked graph map and grammar evidence together
@DataClass(frozen=True, slots=True)
class FrontRead:
    GraphValue: FrontGraph
    MapValue: MapSnapshot
    UsageValue: BodyUsage
