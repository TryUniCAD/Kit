from dataclasses import dataclass as MakeDataClass
from math import isclose


# each sized datum is independently constrained by the reconstructed analytic body
@MakeDataClass(frozen=True, slots=True)
class DatumDisplay:
    CenterValue: tuple[float, float, float]
    BordersValue: tuple[float, float, float, float]
    LabelValue: tuple[float, float, float]
    Tolerance: float

    # display comparison permits only the rounding of the reconstructed body scale
    def IsClose(self, Actual: tuple[float, ...], Expected: tuple[float, ...]) -> bool:
        return len(Actual) == len(Expected) and all(
            isclose(First, Other, rel_tol=0.0, abs_tol=self.Tolerance)
            for First, Other in zip(Actual, Expected, strict=True)
        )
