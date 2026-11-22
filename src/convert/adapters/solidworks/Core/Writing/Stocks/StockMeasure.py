from dataclasses import dataclass as DataClass


# exact publication evidence retains the native build result and actual document identity
@DataClass(frozen=True, slots=True)
class StockMeasure:
    EpochValue: int
    LocatorValue: str
    SizeValue: int
    CandidateSha: str
    ResultSha: str
    EditSha: str
    ReopenSha: str
