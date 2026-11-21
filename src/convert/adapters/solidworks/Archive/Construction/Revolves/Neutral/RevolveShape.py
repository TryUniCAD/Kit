from dataclasses import dataclass as DataClass


# selected construction geometry must remain distinct from the real closed body contour throughout native construction
@DataClass(frozen=True, slots=True)
class RevolveShape:
    VerticesValue: tuple[tuple[float, float], ...]
    AxisStart: tuple[float, float]
    AxisEnd: tuple[float, float]
    AxisEntityId: str
