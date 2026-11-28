from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# header collections can be typed nodes or embedded records without changing their logical ownership
def FieldRecord(Value: object) -> Mapping[str, object]:
    return Value.FieldsValue if isinstance(Value, ArchiveNode) else RequireRecord(Value)
