from collections import Counter
from dataclasses import dataclass as DataClass, field as DataField


# actual grammar reachability must remain separate from globally available schema declarations
@DataClass(slots=True)
class BodyUsage:
    SchemaCalls: Counter[str] = DataField(default_factory=Counter[str])
    FieldCalls: Counter[str] = DataField(default_factory=Counter[str])
    MissingNames: set[str] = DataField(default_factory=set[str])
    SchemaPath: list[str] = DataField(default_factory=list[str])
    FieldPath: list[str] = DataField(default_factory=list[str])
    IsComplete: bool = False
    ByteFields: list[dict[str, object]] = DataField(
        default_factory=list[dict[str, object]]
    )
