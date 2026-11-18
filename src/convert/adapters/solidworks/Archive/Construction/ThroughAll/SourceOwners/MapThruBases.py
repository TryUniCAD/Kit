from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
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


# generated symbol correspondence must distinguish the stock atom from the final body that native regeneration has yet to create
def MapThruBases(
    InputValue: ThruOwnerInput,
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    StockValue: ExtrusionGraph,
    CutValue: CutGraph,
    ScopeValue: StockBodyGraph,
) -> tuple[OwnerBind, ...]:
    Stock, RefsValue = InputValue.ShapeValue.StockValue, InputValue.RefsValue
    RootValue, CutProfile = SystemValue.RootValue, CutValue.ProfileValue
    Circle = CutProfile.GeometryValue
    if type(Circle) is not CircleGraph:
        raise ValueError("generated cut lost its actual circle and centre owners")
    Result = tuple(
        Binding
        for Plane in InputValue.PlaneValues
        for Binding in (
            OwnerBind(
                Plane.PlaneId,
                "datum",
                RootValue,
                SystemValue.SystemValues.PlaneValues[Plane.AxisValue],
            ),
            OwnerBind(
                Plane.FeatureId,
                "datum_feature",
                RootValue,
                SystemValue.SystemValues.PlaneValues[Plane.AxisValue],
            ),
        )
    )
    return Result + (
        OwnerBind(
            RefsValue.StockProfileId,
            "profile_feature",
            RootValue,
            ProfileValue.ProfileValue,
        ),
        OwnerBind(
            RefsValue.CutProfileId,
            "profile_feature",
            RootValue,
            CutProfile.ProfileValue,
        ),
        OwnerBind(
            Stock.SketchId,
            "sketch",
            ProfileValue.ProfileValue,
            ProfileValue.GeometryValue.SketchValue,
        ),
        OwnerBind(
            RefsValue.CutSketchId, "sketch", CutProfile.ProfileValue, Circle.SketchValue
        ),
        OwnerBind(Stock.FeatureId, "join", RootValue, StockValue.FeatureValue),
        OwnerBind(RefsValue.CutFeatureId, "cut", RootValue, CutValue.FeatureValue),
        OwnerBind(
            Stock.ParameterId,
            "driving_length",
            StockValue.FeatureValue,
            StockValue.DimensionsValue[0].ParameterValue,
        ),
        OwnerBind(RefsValue.CircleId, "circle", Circle.SketchValue, Circle.ArcValue),
        OwnerBind(
            RefsValue.CenterId, "circle_center", Circle.SketchValue, Circle.CenterValue
        ),
        OwnerBind(
            RefsValue.ScopeId,
            "selected_stock",
            CutValue.FeatureValue,
            ScopeValue.WrapperValue,
        ),
        OwnerBind(
            Stock.BodyId,
            "final_body_producer_pending_regeneration",
            CutValue.FeatureValue,
            CutValue.FeatureValue,
        ),
    )
