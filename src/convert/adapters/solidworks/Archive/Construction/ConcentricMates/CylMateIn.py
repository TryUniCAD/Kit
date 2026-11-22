from dataclasses import dataclass as DataClass


# ordinary concentric publication keeps ordered endpoint intent separate from the child kernel carrier
@DataClass(frozen=True, slots=True)
class CylMateIn:
    NameValue: str
    AlignmentCode: int
    RotationLocked: bool
    FixedIndex: int
    LocalAxes: tuple[tuple[float, float, float], tuple[float, float, float]] | None = (
        None
    )
