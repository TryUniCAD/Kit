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
