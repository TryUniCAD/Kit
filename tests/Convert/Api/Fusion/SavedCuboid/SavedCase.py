from dataclasses import dataclass as MakeDataClass


# fixed capture identities keep public compatibility checks bound to the observed vendor inputs
@MakeDataClass(frozen=True, slots=True)
class SavedCase:
    FileName: str
    DigestValue: str
    WidthMm: float
    DepthMm: float
    HeightMm: float
