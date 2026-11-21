from dataclasses import dataclass as DataClass


# the complete neutral projection must retain modeled semantic identities and dimensions before native allocation begins
@DataClass(frozen=True, slots=True)
class BlindPlan:
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
    DepthName: str = "D1"
    SketchDriverNames: tuple[str, str] = ("D1", "D2")
    PrincipalAxis: str = "z"
    Reversed: bool = False

    # the actual principal axis determines the sketch support and plane frame
    @property
    def AxisValue(self) -> str:
        return self.PrincipalAxis

    # the admitted line loop boss has only its one active depth
    @property
    def SecondDepth(self) -> None:
        return None
