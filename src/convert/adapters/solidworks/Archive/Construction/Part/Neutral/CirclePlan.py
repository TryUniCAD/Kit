from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)


# the analytic profile preserves the actual support and both independently editable owners
@DataClass(frozen=True, slots=True)
class CirclePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
    AxisValue: str
    SketchId: str
    SketchName: str
    FeatureId: str
    FeatureName: str
    ParameterId: str
    BodyId: str
    CircleValue: CircleInput
    RadialId: str
    IsDiameter: bool
    TextPoint: tuple[float, float]
    DepthValue: float
    IsReversed: bool
