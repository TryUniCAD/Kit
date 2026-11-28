from dataclasses import dataclass as DataClass


# independent native clock owners must not be collapsed into one document creation event
@DataClass(frozen=True, slots=True)
class HeaderClocks:
    CreatedAt: int
    ArchiveAt: int
    UpdatedAt: int

    # the measured modern domain avoids unqualified unset time and calendar sentinel repair branches
    def __post_init__(self) -> None:
        if any(
            type(TimeValue) is not int or not 946684800 <= TimeValue < 4102444800
            for TimeValue in (self.CreatedAt, self.ArchiveAt, self.UpdatedAt)
        ):
            raise ValueError("header clocks require explicit modern wall seconds")
