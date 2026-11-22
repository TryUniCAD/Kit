from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the standard sweep serializes its ordinary body feature and then its owned standard definition
KSweepFeature = (
    NativeField("Base", "moBodyFeature_c"),
    NativeField("Embed", "f820", "sweep.data19000"),
    NativeField("Scalar", "fc0c", "i32"),
    NativeField("Scalar", "fc10", "u8"),
    NativeField("Scalar", "fc14", "u8"),
    NativeField("Scalar", "fc18", "u8"),
    NativeField("Scalar", "fc1c", "u8"),
    NativeField("Scalar", "f80c", "u8"),
    NativeField("Scalar", "fc20", "u8"),
    NativeField("Scalar", "fc24", "u8"),
)


# the ordinary swept boss definition owns its two curve collections before the mode controls
KSweepDataHead = (
    NativeField("Embed", "f2c0", "rf.suObArray"),
    NativeField("Embed", "f2e0", "rf.suObArray"),
    NativeField("Embed", "f300", "rf.suObArray"),
    NativeField("Scalar", "f270", "u8"),
    NativeField("Scalar", "f274", "u8"),
    NativeField("Scalar", "f278", "i32"),
    NativeField("Scalar", "f70", "f64"),
    NativeField("Scalar", "f2ac", "u8"),
    NativeField("Scalar", "f2b0", "u8"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f80", "i32"),
    NativeField("Embed", "f98", "suObList"),
    NativeField("Embed", "fe0", "suObList"),
)


# the sole cold standard mode retains typed empty alternatives and native scalar field order
KSweepDataTail = (
    NativeField("Scalar", "f230", "i32"),
    NativeField("Scalar", "f78", "u8"),
    NativeField("Scalar", "f234", "u8"),
    NativeField("Scalar", "f238", "f64"),
    NativeField("Scalar", "f240", "f64"),
    NativeField("Scalar", "f248", "i32"),
    NativeField("Scalar", "f24c", "i32"),
    NativeField("Scalar", "f2b4", "i32"),
    NativeField("Scalar", "f280", "f64"),
    NativeField("Scalar", "f288", "f64"),
    NativeField("Scalar", "f290", "i32"),
    NativeField("Scalar", "f27c", "u8"),
    NativeField("Scalar", "f2a8", "u8"),
    NativeField("Scalar", "f258", "i32"),
    NativeField("Scalar", "f260", "f64"),
    NativeField("Node", "f298", "moTwistDataForBiDirectionalSweep_c"),
    NativeField("Node", "f2a0", "moEndPointRef_w"),
    NativeField("Scalar", "f2b8", "u8"),
    NativeField("Embed", "f320", "rf.suObArray"),
    NativeField("Embed", "f340", "rf.suObArray"),
    NativeField("Scalar", "f3b0", "i32"),
)
