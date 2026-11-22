from dataclasses import dataclass as DataClass
from typing import TypeAlias

# an annotation transform has three ordered signed model axes
KAnnoAxis: TypeAlias = tuple[float, float, float]

# the base view definition keeps the complete rotation in model axes
KAnnoBasis: TypeAlias = tuple[KAnnoAxis, KAnnoAxis, KAnnoAxis]

# the empty ordinary catalog uses the reserved annotation identity
KNoAnno = 199


# catalog inputs retain the name and actual authored orientation separately from cameras
@DataClass(frozen=True, slots=True)
class AnnoViewInput:
    NameValue: str
    BasisValue: KAnnoBasis
