from dataclasses import dataclass as DataClass


# complete style construction requires caller authored localized vocabulary and print settings rather than installed preferences or resource reads
@DataClass(frozen=True, slots=True)
class StyleInput:
    StandardValue: int
    FontName: str
    LineStyleName: str
    LanguageId: int
    PrintWidths: tuple[float, ...]
    ExclusionNames: tuple[str, ...]
    TaskLabels: tuple[str, ...]
    CutlistExpressions: tuple[str, ...]
