from dataclasses import dataclass as MakeDataClass


# recorded native observations keep public geometry checks independent from the new analytic implementation
@MakeDataClass(frozen=True, slots=True)
class RimApiState:
    Volume: float
    AreaValue: float
    Center: tuple[float, ...]
    Lower: tuple[float, ...]
    Upper: tuple[float, ...]
    Parameters: tuple[tuple[str, float], ...]
