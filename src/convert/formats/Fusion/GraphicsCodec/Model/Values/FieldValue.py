from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet


@MakeDataClass(frozen=True, slots=True)
class FieldValue:
    FieldName: str
    DataValue: (
        bool
        | int
        | float
        | str
        | None
        | tuple[float, ...]
        | TextureValue
        | ObjectRef
        | NodeTarget
        | tuple[OverrideSet, ...]
    )
