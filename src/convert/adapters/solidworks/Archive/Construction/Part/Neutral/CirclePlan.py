from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)


# a circle boss preserves its model identities and radial intent without replacing its analytic outline with vertices
@DataClass(frozen=True, slots=True)
class CirclePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
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
