from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the observed bounds record stores ten consecutive doubles in its owning body
KExternalFields = MappingProxyType(
    {
        "mgBBox_c.restore": (
            NativeField("Scalar", "b0", "f64"),
            NativeField("Scalar", "b1", "f64"),
            NativeField("Scalar", "b2", "f64"),
            NativeField("Scalar", "b3", "f64"),
            NativeField("Scalar", "b4", "f64"),
            NativeField("Scalar", "b5", "f64"),
            NativeField("Scalar", "b6", "f64"),
            NativeField("Scalar", "b7", "f64"),
            NativeField("Scalar", "b8", "f64"),
            NativeField("Scalar", "b9", "f64"),
        ),
    }
)
