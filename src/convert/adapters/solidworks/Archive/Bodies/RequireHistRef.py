from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the resolved history pointer uses native read context around one typed node
KHistRefMode = "HistoryComponent"

# the witnessed pointer operator admits the concrete current chain class
KHistChain = RuntimeClass("moChainComponent_c", 1)


# both archive directions must preserve a concrete chain owner through the shared map
def RequireHistRef(ValueData: object) -> ArchiveNode:
    if not isinstance(ValueData, ArchiveNode) or ValueData.ClassValue != KHistChain:
        raise BodyUnsupported("history component requires a schema-one chain component")
    return ValueData
