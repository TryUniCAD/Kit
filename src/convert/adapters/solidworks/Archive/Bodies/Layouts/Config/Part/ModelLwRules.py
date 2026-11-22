from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the lightweight section starts with the actual header handoff and its model fields
KModelLwRules = MappingProxyType(
    {
        "moModel_c.FUN_4c17aa00": (
            NativeField("Direct", ""),
            NativeField("Scalar", "fb0", "i32"),
            NativeField("Scalar", "fb4", "u32"),
            NativeField("Base", "moConcept_c.SerializeLWData"),
        ),
        "moModel_c.FUN_4c22ec80": (
            NativeField("Base", "moModel_c.FUN_4c17aa00"),
            NativeField("Node", "f9b8"),
            NativeField("Node", "f990"),
            NativeField(
                "Branch",
                "moDrawing_c",
                OtherValue=(NativeField("Embed", "fdd0", "moFaceVizProps_c.restore"),),
                ModeValue="Class",
            ),
            NativeField("Scalar", "fd30", "u8"),
            NativeField("Node", "fa70"),
            NativeField("Node", "fdb0"),
            NativeField("Scalar", "has_f7f8", "u8"),
            NativeField(
                "Branch",
                "has_f7f8",
                BodyValue=(NativeField("Embed", "f7f8", "mgBBox_c.restore"),),
                ModeValue="NotEquals",
            ),
            NativeField("Scalar", "fef8", "i32"),
            NativeField(
                "Array",
                "f168",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Node", "value"),
                ),
                CountValue="n168",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "ff18", "i32"),
            NativeField("Scalar", "ff20", "i32"),
            NativeField("Scalar", "ff2c", "i32"),
            NativeField(
                "Array",
                "f178",
                "i32",
                BodyValue=(
                    NativeField("Text", "key"),
                    NativeField("Node", "value"),
                ),
                CountValue="n180",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "ff80", "f64"),
            NativeField("Scalar", "ff88", "f64"),
            NativeField("Embed", "fa98", "moModel_c.FUN_4c22ec20"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "f160", "i32"),
                    NativeField(
                        "Branch",
                        "f160",
                        BodyValue=(
                            NativeField("Embed", "f150", "suDynArray.FUN_4ba47010"),
                        ),
                        ModeValue="NotEquals",
                    ),
                ),
                ModeValue="NotCondition",
                MaskValue=128,
            ),
            NativeField("Scalar", "ff1c", "i32"),
            NativeField("Scalar", "shrinkwrap", "i32"),
            NativeField("Scalar", "defeatured", "i32"),
            NativeField(
                "Branch",
                "shrinkwrap",
                BodyValue=(NativeField("Fail", "moShrinkWrapData_c FUN_4c0c4b80"),),
                ModeValue="NotEquals",
            ),
            NativeField("Scalar", "fd50", "i32"),
            NativeField("Embed", "fc90", "suObList"),
            NativeField("Scalar", "fd58", "i32"),
            NativeField(
                "Array",
                "fcd8",
                "i32",
                BodyValue=(
                    NativeField("Text", "key"),
                    NativeField(
                        "Array",
                        "notes",
                        "i32",
                        BodyValue=(NativeField("Node", "o"),),
                        CountValue="m",
                        ModeValue="Positive",
                    ),
                ),
                CountValue="ncd8",
                ModeValue="Positive",
            ),
            NativeField("Bytes", "f784", MaskValue=16),
            NativeField("Scalar", "f1188", "i32"),
            NativeField("Bytes", "f7a4", MaskValue=16),
            NativeField("Scalar", "f118c", "i32"),
            NativeField("Scalar", "f1190", "i32"),
            NativeField("Scalar", "f1194", "i32"),
            NativeField("Scalar", "has_f1180", "i32"),
            NativeField(
                "Branch",
                "has_f1180",
                BodyValue=(
                    NativeField("Fail", "moComponentImportData_c FUN_4b2b2410"),
                ),
                ModeValue="NotEquals",
            ),
            NativeField("Scalar", "f280", "i32"),
            NativeField("Scalar", "f1300", "u32"),
            NativeField("Scalar", "f1308", "i32"),
            NativeField(
                "Array",
                "f1310",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "key", "u32"),
                    NativeField("Scalar", "value", "i32"),
                ),
                CountValue="n1318",
                ModeValue="Unsigned",
            ),
            NativeField("Node", "f2f8"),
        ),
    }
)
