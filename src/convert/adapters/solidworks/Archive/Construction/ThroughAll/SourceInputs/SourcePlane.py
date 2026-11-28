from dataclasses import dataclass as DataClass


# source datum identities must stay distinct from freshly allocated native plane identifiers
@DataClass(frozen=True, slots=True)
class SourcePlane:
    PlaneId: str
    FeatureId: str
    NameValue: str
    AxisValue: str
