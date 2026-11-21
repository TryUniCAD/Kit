from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the measured embedded pattern shape form selects its point or reference before the vector
KPatternShapeFields = (
    NativeField("Scalar", "f30", "i32"),
    NativeField(
        "Branch",
        "f30",
        BodyValue=(NativeField("Fail", "alternate linear pattern shape form"),),
        ModeValue="NotEquals",
        MaskValue=1,
    ),
    NativeField("Node", "f48", "moDisplayRadialDim_c"),
    NativeField("Scalar", "f98", "i32"),
    NativeField(
        "Branch",
        "f98",
        BodyValue=(NativeField("Embed", "f90", "mgPoint_c.restore"),),
        OtherValue=(NativeField("Node", "f68", "moRefWrapper_c"),),
        ModeValue="Nonzero",
    ),
    NativeField("Embed", "f18", "mgVector_c.restore"),
    NativeField("Scalar", "f9c", "i32"),
)
