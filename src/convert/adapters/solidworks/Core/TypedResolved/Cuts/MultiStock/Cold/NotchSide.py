from dataclasses import dataclass as DataClass

from interchange.geometry.Models.VectorPlane import PlaneVector


# exterior clipping uses the actual local stock side and its inward basis
@DataClass(frozen=True, slots=True)
class NotchSide:
    IndexValue: int
    OffsetValue: float
    StationValue: float
    LengthValue: float
    TangentValue: PlaneVector
    InwardValue: PlaneVector
