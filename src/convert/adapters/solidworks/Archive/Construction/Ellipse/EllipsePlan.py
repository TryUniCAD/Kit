from dataclasses import dataclass as DataClass

# three physical conic stations are sufficient to derive the closed sketch
KEllipStations = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


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
