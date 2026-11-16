from dataclasses import dataclass as DataClass
from typing import Literal


# structural tags need explicit identities before archive maps resolve their meaning
@DataClass(frozen=True, slots=True)
class ArchiveTag:
    KindValue: Literal["Null", "NewClass", "ClassRef", "ObjectRef"]
    IndexValue: int | None
