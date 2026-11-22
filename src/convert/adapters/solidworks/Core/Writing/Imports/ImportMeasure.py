from dataclasses import dataclass as DataClass


# only authenticated archive and observation identities reach native publication
@DataClass(frozen=True, slots=True)
class ImportMeasure:
    SizeValue: int
    CandidateSha: str
    ResultSha: str
    RebuildSha: str
    ReopenSha: str
