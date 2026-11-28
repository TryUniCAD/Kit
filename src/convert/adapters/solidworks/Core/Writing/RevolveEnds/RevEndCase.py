from dataclasses import dataclass as DataClass


# native edit and fresh reopen records attest the same measured complete candidate
@DataClass(frozen=True, slots=True)
class RevEndCase:
    LocatorValue: str
    CandidateSha: str
    EditSha: str
    ReopenSha: str
