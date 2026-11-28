from dataclasses import dataclass as DataClass


# native occurrence colours must retain their words before portable component resolution exists
@DataClass(frozen=True, slots=True)
class OccColour:
    OccurrenceNum: int
    ColourWord: int
