from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankNode import (
    CheckBlankNode,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadLinkedBody import (
    ReadLinkedBody,
)
from convert.adapters.solidworks.Drawing.Definition.Named.Checks.CheckNamedGraph import (
    CheckNamedGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph
from convert.adapters.solidworks.Drawing.Definition.Named.NamedRead import NamedRead


# the named definition must retain actual aliases while applying its own drawing profile
def ReadNamedDef(
    DataValue: bytes, VersionValue: int, OrientationValue: str
) -> NamedRead:
    Document, MapsValue, UsageValue = ReadLinkedBody(DataValue, VersionValue, "named")
    GraphValue = NamedGraph(Document, VersionValue, OrientationValue)
    CheckNamedGraph(GraphValue)
    for NodeValue in WalkDrawNodes(Document):
        CheckBlankNode(NodeValue)
    UsageValue.IsComplete = True
    return NamedRead(GraphValue, MapsValue, UsageValue)
