from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KMaterialFields = MappingProxyType(
    {
        "utLineWidth_c.Serialize0": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
