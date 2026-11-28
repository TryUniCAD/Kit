from dataclasses import dataclass as DataClass


# authored paper choices must stay separate from native bookkeeping and constructor fields
@DataClass(frozen=True, slots=True)
class SheetInput:
    NameValue: str
    PaperSize: str
    NumeratorValue: int
    DenominatorValue: int
    LengthUnit: str
    PropertyView: str
