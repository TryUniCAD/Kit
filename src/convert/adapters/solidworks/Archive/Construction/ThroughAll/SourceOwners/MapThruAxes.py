from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.ExtrusionGraph import (
    ExtrusionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.OwnerBind import (
    OwnerBind,
)


# implicit normal selections are regenerated through actual profile references and datum objects rather than invented native axis features
def MapThruAxes(
    InputValue: ThruOwnerInput,
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    StockValue: ExtrusionGraph,
    CutValue: CutGraph,
) -> tuple[OwnerBind, ...]:
    Result: list[OwnerBind] = []
    Stock = InputValue.ShapeValue.StockValue
    PlaneValue = SystemValue.SystemValues.PlaneValues[Stock.AxisValue]
    ActivePlane = next(
        Value for Value in InputValue.PlaneValues if Value.AxisValue == Stock.AxisValue
    )
    for AxisValue in InputValue.AxisValues:
        IsStock = AxisValue.FeatureId == Stock.FeatureId
        Profile = ProfileValue if IsStock else CutValue.ProfileValue
        Feature = StockValue.FeatureValue if IsStock else CutValue.FeatureValue
        SketchId = Stock.SketchId if IsStock else InputValue.RefsValue.CutSketchId
        if AxisValue.SketchId != SketchId or AxisValue.PlaneId != ActivePlane.PlaneId:
            raise ValueError("source normal selection lost its actual sketch or datum")
        Result.append(
            OwnerBind(
                AxisValue.SelectionId,
                "normal_axis",
                Feature,
                {
                    "profile": Profile.ProfileValue,
                    "reference": Profile.ReferenceValue,
                    "datum": PlaneValue,
                    "normal": Profile.FrameValue.NormalValue,
                },
            )
        )
    return tuple(Result)
