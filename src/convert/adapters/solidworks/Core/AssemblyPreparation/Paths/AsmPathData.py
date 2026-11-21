from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)


# linked native identities must share their authored final directory without retaining any staging path
@DataClass(frozen=True, slots=True)
class AsmPathData:
    ParentValue: SelfFileInput
    ChildValue: SelfFileInput
