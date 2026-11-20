from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot


# definition readback pairs complete model settings with the exact final object map
@DataClass(frozen=True, slots=True)
class ModelDefRead:
    GraphValue: ModelDefGraph
    MapValue: MapSnapshot
    UsageValue: BodyUsage
