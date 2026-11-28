from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# standalone visual references use distinct detached units and the same measured inherited component fields
def DetachVisualRef(UnitValue: ArchiveNode) -> dict[str, object]:
    Fields = CompRefFields(UnitValue)
    Fields["f58"] = ArchiveNode(
        RuntimeClass("moUnitComponent_c", 1), {"owner": None, "has_ext": 0}
    )
    return Fields
