from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Assembly.Assembly import NativeAsmItem


# source selected cylinders need actual occurrence identity separately from their observed world geometry
@DataClass(frozen=True, slots=True)
class CylEndpoint:
    ItemValue: NativeAsmItem
    OriginValue: tuple[float, float, float]
    AxisValue: tuple[float, float, float]
    RadiusValue: float
    StampValue: int
