from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# actual local point coordinates must determine every dimension length and placement projection without saved geometry values
def ReadPointPair(PointValue: ArchiveNode) -> tuple[float, float]:
    FieldsValue = RequireRecord(PointValue.FieldsValue.get("pos"))
    return RequireScalar(FieldsValue.get("x")), RequireScalar(FieldsValue.get("y"))
