from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# material identity precedes the measured texture and rendering options in the actual owner
KMatPropFields = (
    NativeField("Text", "f28"),
    NativeField("Text", "f20"),
    NativeField("Scalar", "f38", "f64"),
    NativeField("Scalar", "f40", "f64"),
    NativeField("Scalar", "f48", "f64"),
    NativeField("Scalar", "f50", "f64"),
    NativeField("Scalar", "f58", "f64"),
    NativeField("Scalar", "f60", "f64"),
    NativeField("Scalar", "has80", "i32"),
    NativeField(
        "Branch",
        "has80",
        BodyValue=(NativeField("Embed", "f80", "uoMaterialTextureProperties.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "f68", "i32"),
    NativeField("Scalar", "f6c", "i32"),
    NativeField("Scalar", "f70", "i32"),
    NativeField("Scalar", "f74", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Text", "f30"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "has90", "i32"),
    NativeField(
        "Branch",
        "has90",
        BodyValue=(NativeField("Embed", "f90", "uoRVAppearanceProperties.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Text", "fb8"),
    NativeField("Scalar", "has98", "i32"),
    NativeField(
        "Branch",
        "has98",
        BodyValue=(NativeField("Fail", "secondary material texture"),),
        ModeValue="Nonzero",
    ),
    NativeField("Embed", "props", "moUserProperty_c.restore"),
)
