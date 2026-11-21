from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AngleGeometry import (
    AngleGeometry,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AnglePlaneInput import (
    AnglePlaneInput,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleArc import (
    MakeAngleArc,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import (
    MakeAngleValue,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# the live angle and its separate display own their actual handles and localized witnesses
def MakeAngleDrive(
    PlaneValue: ArchiveNode,
    InputValue: AnglePlaneInput,
    Geometry: AngleGeometry,
    ViewId: int,
) -> DimensionGraph:
    Parameter = ArchiveNode(RuntimeClass("moAngleParameter_c", 1), {})
    InitNodeMut(Parameter, "D1")
    Parameter.FieldsValue.update(
        owner=PlaneValue, f0c=0, f48=None, f58=InputValue.AngleValue, f68=0
    )
    Dimension = MakeAngleValue(PlaneValue, Parameter)
    First, Second, Center = Geometry.WitnessValues
    Dimension.FieldsValue.update(
        f80=DatumPoint(First),
        fa0=DatumPoint(Second),
        fc0=DatumPoint(Center),
        has_ff0=1,
        ff0=FrameXform(Geometry.DimensionValue),
    )
    Handle = MakeHandleMut(PlaneValue, Dimension)
    Fields = MakeCommonView(
        Handle, InputValue.DesignIntent, InputValue.SelectedLeader, 13
    )
    Fields.update(MakeAngleArc(Geometry, InputValue.AngleValue))
    Cached = RequireRecord(Fields["f5b0"])
    Fields.update(
        owner=PlaneValue,
        f2b0=({"v": ViewId},),
        ff68=DatumPoint(InputValue.ShiftValue),
        f5b0={**Cached, "data": PackValue("<d", InputValue.AngleValue)},
    )
    Display = ArchiveNode(RuntimeClass("moDisplayAngularDim_c", 1), Fields)
    return DimensionGraph(Parameter, Dimension, Handle, Display)
