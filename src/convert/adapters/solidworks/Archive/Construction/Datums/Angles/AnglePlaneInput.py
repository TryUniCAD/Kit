from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)


# native angle construction binds the driving scalar and its explicit presentation
@DataClass(frozen=True, slots=True)
class AnglePlaneInput:
    NameValue: str
    AngleValue: float
    Reversed: bool
    AnnotationName: str
    DesignIntent: bool
    SelectedLeader: int
    ShiftValue: KDatumVector
