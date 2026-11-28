from dataclasses import dataclass as DataClass

from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateEntity import MateEntity


# each endpoint keeps its authored selection and the world line of its actual selected child
@DataClass(frozen=True, slots=True)
class CylMateEnd:
    EntityValue: MateEntity
    OccurrenceValue: ComponentInst
    IndexValue: int
    OriginValue: tuple[float, float, float]
    AxisValue: tuple[float, float, float]
