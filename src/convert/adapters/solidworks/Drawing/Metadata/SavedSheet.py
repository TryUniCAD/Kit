from dataclasses import dataclass as DataClass


# keyword rows carry sheet identity and any referenced model view by name
@DataClass(frozen=True, slots=True)
class SavedSheet:
    IdValue: int
    NameValue: str
    ScaleRatio: tuple[float, float]
    ViewName: str
    ModelName: str
    ConfigName: str
