from dataclasses import dataclass as DataClass

# canonical sweep reads and writes share the same ordinary solid feature name
KSweepBossName = "OrdinarySweptBoss"


# the qualified ordinary scene uses one default configuration and the two canonical sketch roles
@DataClass(frozen=True, slots=True)
class SweepLabels:
    NameValue: str
    ConfigName: str = "Default"
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = "SweepPath"
    FeatureName: str = KSweepBossName
    SectionName: str = "SweepSection"
