from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface


@MakeDataClass(frozen=True, slots=True)
class ChoiceValue:
    ChoiceKey: int | str
    Body: "KGrammarValue"


@MakeDataClass(frozen=True, slots=True)
class SubtypeNode:
    SubtypeName: str
    Body: "KGrammarValue"


@MakeDataClass(frozen=True, slots=True)
class SubtypeRef:
    Family: str
    Index: int


@MakeDataClass(frozen=True, slots=True)
class LoftSubdata:
    SubdataKind: int
    RowCount: int
    ColumnCount: int
    Values: tuple[float, ...]


KGrammarValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    tuple["KGrammarValue", ...],
    ChoiceValue,
    SubtypeNode,
    SubtypeRef,
    LoftSubdata,
    BsCurve,
    BsSurface,
]

KSubtypeValue: TypeAlias = Union[SubtypeNode, SubtypeRef]
