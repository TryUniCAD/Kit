from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# plane endpoint wrappers retain actual component references and their independent native bookkeeping
KWrapperFields = MappingProxyType(
    {
        "moRefWrapper_c": (
            NativeField("Node", "f58", "moCompRefPlane_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail",
                        "ordinary mate endpoint requires a component plane reference",
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("class_of", ("lookup", ("scope",), ("literal", "f58"))),
                    ("literal", "moCompRefPlane_c"),
                ),
            ),
            NativeField("Scalar", "f68", "u16"),
            NativeField("Node", "f60", "moComponent_c"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField(
                "Present",
                "has_f10",
                "u16",
                BodyValue=(NativeField("Embed", "f10", "mgXform_c.restore"),),
            ),
            NativeField(
                "Present",
                "has_f18",
                "u16",
                BodyValue=(NativeField("Embed", "f18", "mgXform_c.restore"),),
            ),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f74", "i32"),
            NativeField("Scalar", "f78", "i32"),
            NativeField("Scalar", "f7c", "i32"),
            NativeField("Scalar", "f50", "i32"),
            NativeField("Scalar", "f70", "i32"),
            NativeField(
                "Branch",
                "ctx874",
                BodyValue=(
                    NativeField(
                        "Present",
                        "has_f80",
                        "i32",
                        BodyValue=(
                            NativeField("Embed", "f80", "moReferencedConfiguration_c"),
                        ),
                    ),
                ),
                ModeValue="Context",
            ),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f30", "i32"),
            NativeField("Scalar", "f98", "i32"),
            NativeField("Scalar", "f38", "i32"),
        ),
        "moSurfaceRef_w": (
            NativeField("Base", "moRefWrapper_c"),
            NativeField("Scalar", "fb0", "f64"),
            NativeField("Scalar", "fb8", "f64"),
            NativeField("Scalar", "fc0", "f64"),
            NativeField("Scalar", "fc8", "f64"),
        ),
        "moPlaneRef_w": (
            NativeField("Base", "moSurfaceRef_w"),
            NativeField("Embed", "fd0", "mgPoint_c.restore"),
            NativeField("Embed", "fe8", "mgVector_c.restore"),
            NativeField("Embed", "f100", "mgXform_c.restore"),
            NativeField("Embed", "f188", "mgPoint_c.restore"),
        ),
    }
)
