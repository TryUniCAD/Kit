from dataclasses import dataclass as DataClass


# the qualified ordinary scene uses one default configuration and the two canonical sketch roles
@DataClass(frozen=True, slots=True)
class SweepLabels:
    NameValue: str
    ConfigName: str = "Default"
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = "SweepPath"
    FeatureName: str = "OrdinarySweptBoss"
    SectionName: str = "SweepSection"
