from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KGeometryFields = MappingProxyType(
    {
        "mgMatrix_c.restore": (
            NativeField("Scalar", "m0", "f64"),
            NativeField("Scalar", "m1", "f64"),
            NativeField("Scalar", "m2", "f64"),
            NativeField("Scalar", "m3", "f64"),
            NativeField("Scalar", "m4", "f64"),
            NativeField("Scalar", "m5", "f64"),
            NativeField("Scalar", "m6", "f64"),
            NativeField("Scalar", "m7", "f64"),
            NativeField("Scalar", "m8", "f64"),
        ),
        "mgXform_c.restore": (
            NativeField("Scalar", "has_matrix", "u8"),
            NativeField(
                "Branch",
                "has_matrix",
                BodyValue=(NativeField("Embed", "f08", "mgMatrix_c.restore"),),
                ModeValue="NotEquals",
            ),
            NativeField("Scalar", "f58", "f64"),
            NativeField("Scalar", "f60", "f64"),
            NativeField("Scalar", "f68", "f64"),
            NativeField("Scalar", "f70", "f64"),
            NativeField("Scalar", "f78", "u8"),
            NativeField(
                "Branch",
                "f78",
                BodyValue=(NativeField("Embed", "f80", "mgMatrix5_c.restore"),),
                ModeValue="BitsEqual",
                MaskValue=240,
                CompareValue=64,
            ),
            NativeField(
                "Branch",
                "f78",
                BodyValue=(NativeField("Embed", "f80", "mgPerspInfo_c.restore"),),
                ModeValue="BitsEqual",
                MaskValue=240,
                CompareValue=32,
            ),
            NativeField(
                "Branch",
                "f78",
                BodyValue=(NativeField("Embed", "f80", "mgPerspInfoBase_c.restore"),),
                ModeValue="BitsEqual",
                MaskValue=240,
                CompareValue=16,
            ),
        ),
    }
)
