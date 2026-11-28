from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# native measurements must remain independent of the reader under qualification
@MakeDataClass(frozen=True, slots=True)
class OffsetCase:
    Source: FilePath
    Digest: str
    Reading: dict[str, object]
