from dataclasses import dataclass as DataClass


# authored visibility must identify named occurrences before the assembly allocates its archive identifiers
@DataClass(frozen=True, slots=True)
class AsmDisplayIn:
    NameValue: str
    VisibilityValues: tuple[tuple[str, bool], ...]
