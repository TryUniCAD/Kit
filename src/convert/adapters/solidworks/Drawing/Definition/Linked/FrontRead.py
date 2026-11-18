from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadGraphRender import (
    ReadGraphRender,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.RenderState import (
    RenderState,
)
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
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph


# complete readback must carry its actual linked graph map and grammar evidence together
@DataClass(frozen=True, slots=True)
class FrontRead:
    GraphValue: FrontGraph
    MapValue: MapSnapshot
    UsageValue: BodyUsage

    # readers must expose retained native identities separately from portable edge semantics
    @property
    def DetailingMap(self) -> DetailMap:
        FieldsValue = self.GraphValue.DocumentValue.FieldsValue
        ModelValue = NeedDetailNode(FieldsValue.get("model"), "moDrawing_c")
        return ReadDetailMap(ModelValue, self.GraphValue.VersionValue)

    # cache presence and native colours must remain visible on the actual owned view
    @property
    def Rendering(self) -> RenderState:
        return ReadGraphRender(
            self.GraphValue.DocumentValue, self.GraphValue.VersionValue
        )

    # complete byte grammar cannot silently imply projection of native model edge identities
    @property
    def Unprojected(self) -> tuple[str, ...]:
        return self.DetailingMap.Unprojected + self.Rendering.Unprojected
