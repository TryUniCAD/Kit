from dataclasses import dataclass as DataClass


# authenticated records stay separate from the neutral model and generated archive input
@DataClass(frozen=True, slots=True)
class RevEvidence:
    WrittenAt: int
    Summary: dict[str, object]
    Report: dict[str, object]
    Job: dict[str, object]
