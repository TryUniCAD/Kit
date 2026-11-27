from dataclasses import dataclass as DataClass
from pathlib import Path as FilePath


# source bound expectations keep geometry assertions independent from the reader output
@DataClass(frozen=True, slots=True)
class ReverseCase:
    SourcePath: FilePath
    IsReversed: bool
    DepthMm: float
    VolumeMm: float
    Centroid: tuple[float, ...]
    CornerCount: int
