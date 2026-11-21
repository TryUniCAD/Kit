from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)


# angle presentation needs its actual parameter identity without repeating the driving angle
@DataClass(frozen=True, slots=True)
class PatAngleStyle:
    ParamId: str
    AnnotationName: str
    DesignIntent: bool
    SelectedLeader: int
    ShiftValue: KDatumVector
