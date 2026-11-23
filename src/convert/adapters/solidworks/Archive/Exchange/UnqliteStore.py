from dataclasses import dataclass as DataClass


# consumers need only the time word and live records to construct a fresh exchange store
@DataClass(frozen=True, slots=True)
class UnqliteStore:
    ClockValue: int
    Records: tuple[tuple[bytes, bytes], ...]
