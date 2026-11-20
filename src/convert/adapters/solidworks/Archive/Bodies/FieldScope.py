from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass as DataClass, field as DataField


# embedded and repeated fields need inherited lookup without copying lazy model mappings
@DataClass(slots=True)
class FieldScope:
    FieldsValue: MutableMapping[str, object]
    ParentValue: FieldScope | None = None
    IndexValue: int | None = None
    ValuesValue: dict[str, object] = DataField(default_factory=dict[str, object])
