from dataclasses import dataclass as DataClass


# implicit sketch normal selections need actual source operation profile and plane ownership rather than discarded query strings
@DataClass(frozen=True, slots=True)
class SourceAxis:
    SelectionId: str
    FeatureId: str
    SketchId: str
    PlaneId: str
