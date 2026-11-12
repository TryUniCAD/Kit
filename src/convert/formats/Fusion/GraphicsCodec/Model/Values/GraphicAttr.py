from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue


@MakeDataClass(frozen=True, slots=True)
class GraphicAttr:
    ClassName: str
    Priority: int
    WinTies: bool
    Fields: tuple[FieldValue, ...]
