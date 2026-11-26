from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import (
    MakePlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# principal tangent axes come from the actual typed datum transform rather than private builder annotations
def ReadDatumFrame(Datum: ArchiveNode) -> tuple[PlaneFrame, int]:
    Geometry = RequireNode(Datum.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c")
    Normal = ReadVector(Geometry.FieldsValue.get("normal"))
    AxesValue = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    if Normal not in AxesValue:
        raise ValueError("mate datum requires a positive canonical principal normal")
    Matrix, Offset = ReadRigidXform(RequireRecord(Geometry.FieldsValue.get("f20")))
    Origin = ReadVector(Geometry.FieldsValue.get("root"))
    if Origin != (0.0, 0.0, 0.0) or Offset != (0.0, 0.0, 0.0):
        raise ValueError("principal mate datum must retain its origin plane frame")
    Frame = MakePlaneFrame(
        Origin, (Matrix[0], Matrix[3], Matrix[6]), (Matrix[1], Matrix[4], Matrix[7])
    )
    if Frame.NormalValue != Normal:
        raise ValueError("principal mate datum transform contradicts its normal")
    return Frame, AxesValue.index(Normal) + 1
