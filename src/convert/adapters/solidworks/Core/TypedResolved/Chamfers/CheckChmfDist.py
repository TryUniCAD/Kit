from math import dist as Distance

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# dimension witnesses must come from finite coordinates in their owned typed record
def ChmfViewPoint(NodeValue: ArchiveNode, FieldName: str) -> KDatumVector:
    PointValue = NativeRecord(NodeValue.FieldsValue.get(FieldName))
    return (
        RequireScalar(PointValue.get("x")),
        RequireScalar(PointValue.get("y")),
        RequireScalar(PointValue.get("z")),
    )


# independent lengths require a signed frame whose translation derives from the actual selected edge and setback
def CheckChmfDist(
    Driver: ChmfDriver,
    EdgeCenter: KDatumVector,
    Basis: tuple[KDatumVector, KDatumVector, KDatumVector],
) -> KDatumVector:
    AxisU, AxisV, Normal = Basis
    Anchor = DatumOffset(EdgeCenter, AxisU, -Driver.ValueSi)
    Dimension = Driver.DimensionNode
    Fields = Dimension.FieldsValue
    if (
        Distance(ChmfViewPoint(Dimension, "f80"), Anchor) > 1e-12
        or Distance(ChmfViewPoint(Dimension, "fa0"), EdgeCenter) > 1e-12
        or Fields.get("has_fe0") != 1
        or Fields.get("has_ff0") != 1
        or ChmfViewPoint(Dimension, "fe0") != AxisU
        or ChmfViewPoint(Dimension, "fe8") != AxisV
    ):
        raise ValueError("chamfer length witnesses differ from their signed edge frame")
    Matrix, Shift = ReadRigidXform(NativeRecord(Fields.get("ff0")))
    Expected, ExpectedShift = ReadRigidXform(
        FrameXform(PlaneFrame(Anchor, AxisU, AxisV, Normal))
    )
    if Matrix != Expected or Distance(Shift, ExpectedShift) > 1e-12:
        raise ValueError("chamfer length value has an alternate stored frame")
    return Anchor
