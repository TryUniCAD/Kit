from dataclasses import dataclass as DataClass


# the fresh revolve must retain actual neutral owners and dimensions before allocating any native identity
@DataClass(frozen=True, slots=True)
class RevolvePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
    SketchName: str
    FeatureName: str
    VerticesValue: tuple[tuple[float, float], ...]
    AxisStart: tuple[float, float]
    AxisEnd: tuple[float, float]
    AngleValue: float
    IsReverse: bool
    SketchId: str
    FeatureId: str
    ParameterId: str
    BodyId: str
    SelectionId: str
    AxisEntityId: str

    # the qualified profile uses its actual canonical front support without accepting another plane by label
    @property
    def AxisValue(self) -> str:
        return "z"
