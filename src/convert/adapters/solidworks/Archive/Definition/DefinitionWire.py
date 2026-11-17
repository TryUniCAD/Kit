from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot


# complete stream evidence must retain its derived object map and actual serializer usage
@DataClass(frozen=True, slots=True)
class DefinitionWire:
    OutputValue: bytes
    MapValue: MapSnapshot
    UsageValue: BodyUsage
