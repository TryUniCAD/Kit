from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumLine import (
    DatumLine,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.PatDirLine import (
    PatDirLine,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatFrame import (
    ReadPatFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the line uses the selected plane display bounds and the native ordered corner calculation
def ReadPatDir(PlaneValue: ArchiveNode) -> PatDirLine:
    RequireRootNode(PlaneValue, "moRefPlane_c")
    Geometry = ArchiveNode.RequireNode(PlaneValue.FieldsValue.get("f6f8"))
    RequireRootNode(Geometry, "moConstraintCoincLineAtAnglePlaneRefplaneData_c")
    Fields = Geometry.FieldsValue
    if FieldInt(PlaneValue.FieldsValue, "f2b0") != 19000 or tuple(
        FieldInt(Fields, KeyValue) for KeyValue in ("f54", "f58", "f5c", "f148")
    ) != (-4, -4, 22, -3):
        raise ValueError("pattern direction requires its own ordinary angular datum")
    Borders = tuple(RequireScalar(Fields.get(f"b{Index}")) for Index in range(4))
    Center, Direction, SpanValue = DatumLine(
        ReadPatFrame(Fields), (Borders[0], Borders[1], Borders[2], Borders[3])
    )
    return PatDirLine(Center, Direction, SpanValue)
