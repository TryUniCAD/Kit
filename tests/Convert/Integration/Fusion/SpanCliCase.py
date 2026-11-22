from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# native observations remain independent of decoder output across public cli invocations
@MakeDataClass(frozen=True, slots=True)
class SpanCliCase:
    Source: FilePath
    Digest: str
    SideMode: str
    Volume: float
    AreaValue: float
    Minimum: tuple[float, ...]
    Maximum: tuple[float, ...]
    TimelineCount: int
    CaseName: str
