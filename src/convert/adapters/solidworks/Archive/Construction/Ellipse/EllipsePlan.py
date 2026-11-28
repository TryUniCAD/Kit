from dataclasses import dataclass as DataClass


# the bounded ellipse keeps authored labels and signed stations available to every part owner
@DataClass(frozen=True, slots=True)
class EllipsePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
    SketchName: str
    FeatureName: str
    DepthValue: float
    CenterValue: tuple[float, float]
    MajorValue: tuple[float, float]
    MinorValue: tuple[float, float]
    AxisValue: str = "z"
    SecondDepth: None = None
