from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankNode import (
    CheckBlankNode,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadLinkedBody import (
    ReadLinkedBody,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontGraph import (
    CheckFrontGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontRead import FrontRead


# the front definition must retain actual aliases while applying its own drawing profile
def ReadFrontDef(DataValue: bytes, VersionValue: int) -> FrontRead:
    Document, MapsValue, UsageValue = ReadLinkedBody(DataValue, VersionValue, "front")
    GraphValue = FrontGraph(Document, VersionValue)
    CheckFrontGraph(GraphValue)
    for NodeValue in WalkDrawNodes(Document):
        CheckBlankNode(NodeValue)
    UsageValue.IsComplete = True
    return FrontRead(GraphValue, MapsValue, UsageValue)
