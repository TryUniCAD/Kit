from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the common surface wrapper stores its geometric scalar state before the concrete surface fields
KSurfaceTail = (
    NativeField("Scalar", "fb0", "f64"),
    NativeField("Scalar", "fb8", "f64"),
    NativeField("Scalar", "fc0", "f64"),
    NativeField("Scalar", "fc8", "f64"),
)
