from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue


@MakeDataClass(frozen=True, slots=True)
class FieldValue:
    FieldName: str
    DataValue: bool | int | float | str | None | tuple[float, ...] | TextureValue
