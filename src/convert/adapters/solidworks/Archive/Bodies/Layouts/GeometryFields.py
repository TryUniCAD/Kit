from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native field order is shared by both archive directions without document supplied programs
KGeometryFields = MappingProxyType(
    {
        "mgVector_c.restore": (
            NativeField("Scalar", "x", "f64"),
            NativeField("Scalar", "y", "f64"),
            NativeField("Scalar", "z", "f64"),
        ),
    }
)
