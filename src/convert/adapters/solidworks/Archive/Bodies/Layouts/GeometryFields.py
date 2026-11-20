from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# embedded vector fields share their stored binary64 component order
KGeometryFields = MappingProxyType(
    {
        "mgVector_c.restore": (
            NativeField("Scalar", "x", "f64"),
            NativeField("Scalar", "y", "f64"),
            NativeField("Scalar", "z", "f64"),
        ),
    }
)
