from __future__ import annotations

from dataclasses import dataclass as DataClass
from typing import Literal


# field vocabulary separates native serialization rules from document supplied values
@DataClass(frozen=True, slots=True)
class NativeField:
    KindValue: Literal[
        "Scalar",
        "Text",
        "Node",
        "Base",
        "Embed",
        "Array",
        "Branch",
        "Context",
        "Mask",
        "Virtual",
        "Boolean",
        "Present",
        "Fail",
        "Validate",
        "Section",
        "Direct",
        "Bytes",
        "Length",
        "Repeat",
        "Normalize",
        "GhostCount",
        "MassCaches",
        "BBoxCache",
        "DirectNode",
    ]
    NameValue: str
    TypeValue: str = ""
    BodyValue: tuple[NativeField, ...] = ()
    OtherValue: tuple[NativeField, ...] = ()
    CountValue: str = ""
    ModeValue: str = ""
    MaskValue: int = 0
    OtherName: str = ""
    CompareValue: int = 0
