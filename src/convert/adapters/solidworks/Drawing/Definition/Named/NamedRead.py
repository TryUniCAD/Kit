from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailMap import DetailMap
from convert.adapters.solidworks.Drawing.Definition.Detailing.ReadDetailMap import (
    ReadDetailMap,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailNode import (
    NeedDetailNode,
)
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

    # readers must expose retained native identities separately from portable edge semantics
    @property
    def DetailingMap(self) -> DetailMap:
        FieldsValue = self.GraphValue.DocumentValue.FieldsValue
        ModelValue = NeedDetailNode(FieldsValue.get("model"), "moDrawing_c")
        return ReadDetailMap(ModelValue, self.GraphValue.VersionValue)

    # complete byte grammar cannot silently imply projection of native model edge identities
    @property
    def Unprojected(self) -> tuple[str, ...]:
        return self.DetailingMap.Unprojected
