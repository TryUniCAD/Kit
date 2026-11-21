from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlNumbers import (
    XmlNumbers,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# instance xml projects the actual native rigid occurrence transform into its independent homogeneous row vocabulary with unit scale
def XmlPoseText(Reference: ArchiveNode) -> str:
    FieldsValue = FieldRecord(Reference.FieldsValue["f360"])
    MatrixValue, PositionValue = ReadRigidXform(FieldsValue)
    return XmlNumbers(
        (
            *MatrixValue[:3],
            0,
            *MatrixValue[3:6],
            0,
            *MatrixValue[6:],
            0,
            *PositionValue,
            1,
        )
    )
