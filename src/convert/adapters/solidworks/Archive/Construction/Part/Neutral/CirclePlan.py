from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)


# a circle boss preserves its model identities and radial intent without replacing its analytic outline with vertices
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
    EndValue: BossEndInput

    # the shared part archive exposes the actual primary driving length
    @property
    def DepthValue(self) -> float:
        return self.EndValue.DepthValue

    # only an active second end supplies another independent dimension keyword
    @property
    def SecondDepth(self) -> float | None:
        return self.EndValue.SecondDepth
