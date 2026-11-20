from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# line width styles retain their signed selector before the stored float
KMaterialFields = MappingProxyType(
    {
        "utLineWidth_c.Serialize0": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
