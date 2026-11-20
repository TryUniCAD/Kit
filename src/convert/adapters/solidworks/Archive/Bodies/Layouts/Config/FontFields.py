from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# line font records share their untagged width layout across ordinary archive owners
KFontFields = MappingProxyType(
    {
        "uiLFConfig_c": (
            NativeField("Text", "f08"),
            NativeField("Embed", "f10", "utLineWidth_c.Serialize.2.0"),
            NativeField("Scalar", "f18", "i16"),
        ),
        "utLineWidth_c.Serialize.2.0": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
