from convert.adapters.solidworks.Archive.Construction.Part.Neutral.IsCircDiameter import (
    IsCircDiameter,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Sweeps.ReadSwDrivers import (
    ReadSwLength,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter


# no secondary construction entity state may be replaced by a synthesized native sketch
def GetSwEntity(SketchValue: Sketch) -> SketchEntity:
    if (
        SketchValue.suppressed
        or SketchValue.attributes
        or len(SketchValue.entities) != 1
    ):
        raise ValueError("sweep requires one active analytic entity in each sketch")
    EntityValue = SketchValue.entities[0]
    if EntityValue.construction or EntityValue.fixed or EntityValue.attributes:
        raise ValueError(
            "sweep analytic entities must be ordinary and fixed only through their point relations"
        )
    RulesValue = SketchValue.constraints
    if len({RuleValue.id for RuleValue in RulesValue}) != len(RulesValue) or any(
        RuleValue.suppressed
        or RuleValue.driving is not True
        or RuleValue.attributes
        or RuleValue.provenance is not None
        for RuleValue in RulesValue
    ):
        raise ValueError(
            "sweep sketch relations must be distinct active driving and portable"
        )
    return EntityValue


# the section is a full fixed centre circle with one editable diameter on that circle
def ReadSwSection(SketchValue: Sketch, DriverValue: Parameter) -> CircleGeometry:
    EntityValue = GetSwEntity(SketchValue)
    GeometryValue = EntityValue.geometry
    if (
        EntityValue.kind != GeometryKind.KCircle
        or type(GeometryValue) is not CircleGeometry
        or SketchValue.closed_profile_entity_ids != ((EntityValue.id,),)
        or not IsCircDiameter(SketchValue, EntityValue.id, DriverValue.id)
    ):
        raise ValueError(
            "sweep section requires its actual fixed centre circle with a diameter driver"
        )
    CenterValue = ReadSwPoint(GeometryValue.Center)
    RadiusValue = RequireScalar(GeometryValue.Radius) / 1000.0
    if ReadSwLength(DriverValue) != RadiusValue * 2:
        raise ValueError("sweep diameter driver disagrees with its circle")
    return CircleGeometry(CenterValue, RadiusValue)


# fixing the path start and two point relations preserves the actual supported arc solver intent
def CheckSwArcRules(SketchValue: Sketch, EntityId: str, DriverId: str) -> None:
    CenterRef = ConstraintRef(EntityId, "center")
    StartRef = ConstraintRef(EntityId, "start")
    EndRef = ConstraintRef(EntityId, "end")
    Expected = {
        ("fixed", (StartRef,), None),
        ("vertical", (CenterRef, StartRef), None),
        ("horizontal", (EndRef, CenterRef), None),
        ("radius", (ConstraintRef(EntityId),), DriverId),
    }
    RulesValue = SketchValue.constraints
    Actual = {
        (RuleValue.kind, RuleValue.references, RuleValue.parameter_id)
        for RuleValue in RulesValue
    }
    if len(RulesValue) != len(Expected) or Actual != Expected:
        raise ValueError(
            "sweep path requires exact origin and orthogonal point relations and its actual D1 radius"
        )


# preserve both arc endpoints in the neutral angle orientation and crosscheck the actual radial value
def ReadSwPath(SketchValue: Sketch, DriverValue: Parameter) -> ArcGeometry:
    EntityValue = GetSwEntity(SketchValue)
    GeometryValue = EntityValue.geometry
    if (
        EntityValue.kind != GeometryKind.KArcGeometry
        or type(GeometryValue) is not ArcGeometry
        or SketchValue.closed_profile_entity_ids
    ):
        raise ValueError("sweep path requires its actual open analytic arc")
    CheckSwArcRules(SketchValue, EntityValue.id, DriverValue.id)
    CenterValue = ReadSwPoint(GeometryValue.Center)
    RadiusValue = RequireScalar(GeometryValue.Radius) / 1000.0
    if ReadSwLength(DriverValue) != RadiusValue:
        raise ValueError("sweep radius driver disagrees with its arc")
    return ArcGeometry(
        CenterValue, RadiusValue, GeometryValue.StartAngle, GeometryValue.EndAngle
    )


# canonical neutral coordinates must retain both individually validated authored components
def ReadSwPoint(PointValue: PlaneVector) -> PlaneVector:
    if type(PointValue) is not PlaneVector:
        raise ValueError("sweep sketch geometry requires an actual planar point")
    return PlaneVector(
        RequireScalar(PointValue.XCoord) / 1000.0,
        RequireScalar(PointValue.YCoord) / 1000.0,
    )
