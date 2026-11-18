from dataclasses import dataclass as DataClass


# authored mate endpoints must identify an actual direct occurrence and a qualified principal datum without relying on their position in another mate
@DataClass(frozen=True, slots=True)
class PlaneEndIn:
    OccurrenceIndex: int
    AxisValue: str

    # malformed indices and unqualified datum families must fail before any parent or wrapper state can be allocated
    def __post_init__(self) -> None:
        if type(self.OccurrenceIndex) is not int or self.OccurrenceIndex < 0:
            raise ValueError(
                "principal mate endpoints require nonnegative actual occurrence indices"
            )
        if self.AxisValue not in ("x", "y", "z"):
            raise ValueError(
                "ordinary mate endpoints require a qualified principal plane"
            )
