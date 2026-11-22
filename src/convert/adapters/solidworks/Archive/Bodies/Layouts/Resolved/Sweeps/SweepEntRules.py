from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the sweep profile and path reuse the same live arc handle and radial parameter grammar
KSweepEntRules = MappingProxyType(
    {
        "sgArcHandle": (NativeField("Base", "sk.sgEntHandle.Serialize"),),
        "sgCircleDim": (NativeField("Base", "sk.sgValG1Dim.FUN_4c59ec10"),),
        "sgEntHandle": (NativeField("Base", "sk.sgEntHandle.Serialize"),),
        "sk.sgLogG2Dim.FUN_4c58b970": (
            NativeField("Base", "sk.sgLogDim.Serialize"),
            NativeField("Node", "h1", "sgEntHandle"),
            NativeField("Node", "h2", "sgEntHandle"),
            NativeField("Scalar", "ff8", "u16"),
            NativeField("Scalar", "ffc", "u16"),
            NativeField("Node", "f108"),
            NativeField("Scalar", "f100", "u16"),
            NativeField("Scalar", "f110", "i32"),
            NativeField("Scalar", "f114", "i32"),
            NativeField("Scalar", "f118", "f64"),
            NativeField("Scalar", "f120", "f64"),
            NativeField("Node", "ext1", "sgEntHandle"),
            NativeField("Node", "ext2", "sgEntHandle"),
            NativeField("Node", "ext3", "sgEntHandle"),
            NativeField("Scalar", "f150", "u16"),
            NativeField("Scalar", "f154", "i32"),
        ),
        "sk.sgArc.FUN_4c585150": (
            NativeField("Base", "sk.sgSegment.FUN_4c590920"),
            NativeField("Scalar", "fd8", "i32"),
            NativeField("Scalar", "fdc_s", "u16"),
            NativeField(
                "Branch",
                "fdc_s",
                BodyValue=(NativeField("Scalar", "fdc", "i32"),),
                ModeValue="Equals",
                MaskValue=65535,
            ),
            NativeField("Scalar", "fe0", "i32"),
            NativeField("Scalar", "fe4", "i32"),
            NativeField("Scalar", "fe8", "i32"),
            NativeField("Scalar", "fec", "i32"),
        ),
        "sk.sgValDim.FUN_4c59ea80": (
            NativeField("Base", "sk.sgDim.FUN_4c5868d0"),
            NativeField("Scalar", "fa0", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "xform", "mgXform_c.operator>>"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "fa0")),
                    ("literal", 0),
                ),
            ),
        ),
        "sk.sgValG1Dim.FUN_4c59ec10": (
            NativeField("Base", "sk.sgValDim.FUN_4c59ea80"),
            NativeField("Node", "h1", "sgEntHandle"),
            NativeField("Node", "h2", "sgEntHandle"),
            NativeField("Scalar", "g1", "i32"),
            NativeField("Scalar", "g2", "i32"),
            NativeField("Embed", "dir", "mgVector_c.restore"),
        ),
        "sk.sgEntHandle.Serialize": (
            NativeField("Scalar", "idx", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Scalar", "f18", "i32"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    ("lookup", ("scope",), ("literal", "idx")),
                    ("literal", 30591),
                ),
            ),
            NativeField("Scalar", "f1c", "i32"),
            NativeField("Scalar", "f08", "i32"),
        ),
    }
)
