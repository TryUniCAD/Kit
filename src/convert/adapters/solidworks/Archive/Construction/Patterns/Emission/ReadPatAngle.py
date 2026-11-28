from math import degrees as Degrees

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PatPartGraph import (
    PatPartGraph,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadNodeName,
    RequireNode,
)


# only an actual constrained pattern plane contributes an additional keyword driver
def ReadPatAngle(GraphValue: PatPartGraph) -> tuple[KeywordDim, ...]:
    AngleDrive = GraphValue.AngleValue
    PlaneValue = GraphValue.PlaneValue
    PlaneFields = RequireNode(PlaneValue, "moRefPlane_c").FieldsValue
    if GraphValue.AxisValue is None:
        _ = RequireNode(PlaneFields.get("f6f8"), "moDefaultRefPlnData_c")
        SystemValue = GraphValue.StockValue.SystemValue
        PlanesValue = SystemValue.SystemValues.PlaneValues
        if AngleDrive is not None or PlaneValue not in (
            PlanesValue["x"],
            PlanesValue["y"],
        ):
            raise ValueError(
                "principal pattern Keywords require an existing system datum"
            )
        return ()
    DatumData = RequireNode(
        PlaneFields.get("f6f8"), "moConstraintCoincLineAtAnglePlaneRefplaneData_c"
    )
    if AngleDrive is None:
        raise ValueError("pattern Keywords need the actual local plane angle")
    Angle = RequireNode(AngleDrive.ParameterValue, "moAngleParameter_c")
    if (
        ReadNodeName(Angle) != "D1"
        or Angle.FieldsValue.get("owner") is not PlaneValue
        or DatumData.FieldsValue.get("f150") is not AngleDrive.DisplayValue
    ):
        raise ValueError("pattern Keywords need the actual local plane angle")
    DegreesValue = Degrees(RequireScalar(Angle.FieldsValue.get("f58")))
    return (KeywordDim("D1", DegreesValue, "degree"),)
