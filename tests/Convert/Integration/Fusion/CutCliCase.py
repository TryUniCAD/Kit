from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# independent native observations define the expected public decoding result
@MakeDataClass(frozen=True, slots=True)
class CutCliCase:
    Source: FilePath
    Digest: str
    Volume: float
    AreaValue: float
    Minimum: tuple[float, ...]
    Maximum: tuple[float, ...]
    FaceCount: int
    EdgeCount: int
    VertexCount: int
    StepNames: tuple[str, ...]
    StockParam: str
    CutParam: str
