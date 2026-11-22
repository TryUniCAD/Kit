from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# ordinary configuration keeps each supporting model record typed
KPartRecordRules = MappingProxyType(
    {
        "gcCurvatureObject_c": (
            NativeField("Scalar", "f08", "f64"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Scalar", "f18", "f64"),
            NativeField("Scalar", "f20", "f64"),
            NativeField("Scalar", "f28", "f64"),
            NativeField("Scalar", "f58", "u32"),
            NativeField("Scalar", "f5c", "u32"),
        ),
        "moBodyVizProps_c.FUN_4c240300": (
            NativeField(
                "Array",
                "bodies",
                "i32",
                BodyValue=(
                    NativeField("Embed", "f08", "moVizBodyPropPropElt_c.FUN_4c240770"),
                    NativeField("Node", "f18"),
                    NativeField("Scalar", "f20", "i32"),
                    NativeField("Scalar", "f24", "i32"),
                ),
                CountValue="n08",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "props",
                "i32",
                BodyValue=(
                    NativeField("Embed", "e", "moVizBodyPropPropElt_c.FUN_4c240770"),
                ),
                CountValue="n58",
                ModeValue="Positive",
            ),
        ),
        "moFaceVizProps_c.restore": (
            NativeField(
                "Array",
                "faces",
                "i32",
                BodyValue=(
                    NativeField("Embed", "e", "moVizPropFaceListElt_c.FUN_4c240810"),
                ),
                CountValue="n08",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "props",
                "i32",
                BodyValue=(
                    NativeField("Embed", "e", "moVizPropPropListElt_c.FUN_4c2409d0"),
                ),
                CountValue="n58",
                ModeValue="Positive",
            ),
        ),
        "moForwardedFeatRefsList_c.FUN_4bb5ced0": (NativeField("Base", "suObList"),),
        "moTransRefPlaneData_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "u32"),
            NativeField("Scalar", "f14", "u32"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f1c", "u32"),
        ),
        "moUnitComponent_c": (
            NativeField("Base", "moComponent_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "moUnitComponent_c condition 1"),),
                ModeValue="Condition",
                MaskValue=1,
            ),
            NativeField("Scalar", "has_ext", "u8"),
            NativeField(
                "Branch",
                "has_ext",
                BodyValue=(NativeField("Node", "ext"),),
                ModeValue="NotEquals",
            ),
        ),
        "su_CMapStringToOb.Serialize": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(
                    NativeField("Text", "key"),
                    NativeField("Node", "value"),
                ),
                CountValue="n",
            ),
        ),
    }
)
