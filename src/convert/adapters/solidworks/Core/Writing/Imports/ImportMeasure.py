from dataclasses import dataclass as DataClass


# publication needs the reported creation event and native comparison identities
@DataClass(frozen=True, slots=True)
class ImportMeasure:
    EpochValue: int
    SizeValue: int
    CandidateSha: str
    ResultSha: str
    RebuildSha: str
    ReopenSha: str
