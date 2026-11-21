from collections.abc import Mapping
from dataclasses import dataclass as Dataclass


# the equal length rule retains its ordered solver operands and actual embedded archive ownership
@Dataclass(frozen=True, slots=True)
class LineEqual:
    Indices: tuple[int, int]
    OwnerValue: Mapping[str, object]
