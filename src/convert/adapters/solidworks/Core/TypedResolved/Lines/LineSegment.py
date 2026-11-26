from collections.abc import Mapping
from dataclasses import dataclass as Dataclass


# native line identity must survive independent array order and endpoint numbering
@Dataclass(frozen=True, slots=True)
class LineSegment:
    IndexValue: int
    PermanentId: int
    CreationId: int
    StartValue: int
    EndValue: int
    FieldsValue: Mapping[str, object]
