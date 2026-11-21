from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath


# redundant drawing indexes must derive from one actual generated view reference and selected child configuration
@DataClass(frozen=True, slots=True)
class DrawViewIndex:
    NameValue: str
    PathValue: PureWindowsPath
    ConfigName: str
    ConfigId: int
