from dataclasses import dataclass as MakeDataClass
from pathlib import Path as FilePath


# archive and measurement bindings keep policy acceptance grounded in independently saved source files
@MakeDataClass(frozen=True, slots=True)
class RimPolicyCase:
    CaseName: str
    Source: FilePath
    Digest: str
    Parameters: tuple[tuple[str, float, str, str], ...]
