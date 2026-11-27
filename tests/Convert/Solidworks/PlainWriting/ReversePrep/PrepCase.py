from dataclasses import dataclass as MakeDataClass


# sealed semantic requests keep generated direction checks independent of the preparation implementation
@MakeDataClass(frozen=True, slots=True)
class PrepCase:
    NameValue: str
    Points: tuple[tuple[float, float], ...]
    DepthMm: float
    IsReversed: bool
    VolumeMm: float
    CentroidMm: tuple[float, float, float]
