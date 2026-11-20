from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# label widths need a distinct call site because line fonts use different native restore arguments
KMaterialFields = MappingProxyType(
    {
        "utLineWidth_c.Serialize0": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
