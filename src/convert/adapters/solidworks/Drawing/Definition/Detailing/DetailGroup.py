from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailEntry import (
    DetailEntry,
)


# model keys retain their exact native spelling until child topology can be resolved
@DataClass(frozen=True, slots=True)
class DetailGroup:
    ModelKey: str
    RowsValue: tuple[DetailEntry, ...]
