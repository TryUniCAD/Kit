from dataclasses import dataclass as DataClass


# scoped property dictionaries remain separate until every supplied owner has passed admission
@DataClass(frozen=True, slots=True)
class PartTextData:
    SummaryFields: dict[str, str] | None
    DocumentFields: dict[str, str] | None
    ConfigFields: dict[int, dict[str, str]]
