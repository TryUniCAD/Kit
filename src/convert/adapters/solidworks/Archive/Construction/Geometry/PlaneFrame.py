from dataclasses import dataclass as DataClass


# derived plane geometry retains explicit ordered axes without capturing an encoded transform block
@DataClass(frozen=True, slots=True)
class PlaneFrame:
    OriginValue: tuple[float, float, float]
    AxisU: tuple[float, float, float]
    AxisV: tuple[float, float, float]
    NormalValue: tuple[float, float, float]
