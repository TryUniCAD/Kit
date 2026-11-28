from dataclasses import dataclass as DataClass


# feature atom transient tag and chronological stamp domains must remain independent
@DataClass(frozen=True, slots=True)
class BodyTrackIn:
    FeatureId: int
    FeatureEpoch: int
    FeatureName: str
    ArcMarker: int
    AtomId: int
    BodyStamp: int
    UpdateStamp: int
