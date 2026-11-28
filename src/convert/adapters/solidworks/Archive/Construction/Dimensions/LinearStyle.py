from collections.abc import Mapping
from dataclasses import dataclass as DataClass


# distance display style keeps the actual document projection separate from constructor flags and authored presentation choices
@DataClass(frozen=True, slots=True)
class LinearStyle:
    ProjectionValue: Mapping[str, object]
    UnderText: int
    FlagValue: int
