from dataclasses import dataclass as DataClass


# keyword and property indexes must share one typed sheet identity scale and paper record from the actual generated model
@DataClass(frozen=True, slots=True)
class DrawSheetIndex:
    IdValue: int
    NameValue: str
    PropertyView: str
    WidthValue: float
    HeightValue: float
    Numerator: float
    Denominator: float
