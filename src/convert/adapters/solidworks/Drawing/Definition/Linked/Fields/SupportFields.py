from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# linked drawing owners extend existing resolved bodies without inheriting assembly specific validation
KSupportFields = MappingProxyType(
    {
        "moReferenceInternal_c": (NativeField("Base", "moReference_c"),),
        "moReferenceModel_c": (NativeField("Base", "moReference_c"),),
        "moExtFeature_c": (
            NativeField("Base", "moExtObjectInterface_c.FUN_4c179410"),
            NativeField("Node", "f50"),
            NativeField("Scalar", "f58", "i32"),
        ),
        "moDrawingRefPlnData_c": (
            NativeField("Base", "moRefPlnData_c.serializePlaneData"),
            NativeField("Embed", "f88", "mgXform_c.restore"),
        ),
        "moDisplayProfileFeature_c": (
            NativeField("Base", "moDisplayObject_c.FUN_4ba4d3c0"),
            NativeField(
                "Array",
                "f1e0",
                "i32",
                BodyValue=(NativeField("Scalar", "key", "i32"),),
                CountValue="n1e0",
            ),
            NativeField("Scalar", "f200", "i32"),
        ),
        "suObArray": (NativeField("Base", "rf.suObArray"),),
        "rf.su_CMapObToInt": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Node", "k"), NativeField("Scalar", "v", "i32")),
                CountValue="n",
            ),
        ),
        "viewSketchCache": (
            NativeField("Scalar", "n", "i32"),
            NativeField(
                "Branch",
                "n",
                ModeValue="Nonzero",
                BodyValue=(NativeField("Fail", "drawing view sketch cache entries"),),
            ),
        ),
    }
)
