from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ChamferSpec:
    CornerMm: tuple[float, float]
    DistanceMm: float
    FeatureName: str = "Chamfer"
