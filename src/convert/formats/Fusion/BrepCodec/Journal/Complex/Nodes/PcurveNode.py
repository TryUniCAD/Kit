from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KSubtypeValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class PcurveNode:
    Prefix: EntityPrefix
    Form: int
    Reversed: bool
    Carrier: KSubtypeValue | None
    CurveRef: int
    UOffset: float
    VOffset: float
