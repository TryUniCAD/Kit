from dataclasses import dataclass as DataClass


# current kernel records need named field owners rather than untyped byte offsets
@DataClass(frozen=True, slots=True)
class XmtField:
    NameValue: str
    EncodingValue: str
    PointerClass: int = 0
    CountValue: int = 0
