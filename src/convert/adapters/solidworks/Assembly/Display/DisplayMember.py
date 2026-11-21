from dataclasses import dataclass as DataClass


# occurrence visibility must retain distinct xml and persistent feature identities
@DataClass(frozen=True, slots=True)
class DisplayMember:
    ObjectId: int
    FeatureId: int
    NativeName: str
    Visible: bool
