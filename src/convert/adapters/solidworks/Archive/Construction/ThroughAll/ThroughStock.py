from dataclasses import dataclass as DataClass


# source proven stock retains only actual authored identities geometry and its one total mid plane depth
@DataClass(frozen=True, slots=True)
class ThroughStock:
    NameValue: str
    ConfigName: str
    PlaneName: str
    SketchId: str
    SketchName: str
    FeatureId: str
    FeatureName: str
    ParameterId: str
    BodyId: str
    VerticesValue: tuple[tuple[float, float], ...]
    DepthValue: float
    WidthValue: float
    HeightValue: float
    AxisValue: str
    DepthName: str = "D1"

    # the actual stock has one total mid plane depth and no separately authored second distance
    @property
    def SecondDepth(self) -> None:
        return None
