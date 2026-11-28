from dataclasses import dataclass as DataClass


# the imported solid owns a destination and configuration without needing a sketch or extrusion
@DataClass(frozen=True, slots=True)
class ImportPartPlan:
    NameValue: str
    ConfigName: str
    FeatureName: str = "Imported geometry"
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = ""
    OwnedBody: bool = False
