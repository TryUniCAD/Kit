from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the angle uses a real back annotation view whose basis agrees with its separate display frame
def ReadAngleAnno(
    ModelValue: ArchiveNode, NameValue: str, FrameValue: PlaneFrame
) -> int:
    ViewValue = ReadAnnoView(ModelValue, NameValue).FieldsValue
    Matrix, Offset = ReadRigidXform(RequireRecord(ViewValue.get("f368")))
    Basis = (
        (Matrix[0], Matrix[3], Matrix[6]),
        (Matrix[1], Matrix[4], Matrix[7]),
        (Matrix[2], Matrix[5], Matrix[8]),
    )
    if NameValue != "*Back" or Basis != (
        FrameValue.AxisU,
        FrameValue.AxisV,
        FrameValue.NormalValue,
    ):
        raise ValueError(
            "angular datum requires the actual named Back annotation and its angular dimension frame"
        )
    if Offset != (0.0, 0.0, 0.0):
        raise ValueError("angular annotation requires its actual world anchor")
    return FieldInt(ViewValue, "f360")
