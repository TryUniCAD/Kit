from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# drawing roots retain shared model state before their own active sheet and link collections
KRootFields = MappingProxyType(
    {
        "moDrawing_c": (
            NativeField("Base", "moModel_c.FUN_4c22ec80"),
            NativeField("Base", "moModel_c.FUN_4c234150"),
            NativeField("Node", "f1430"),
            *MakeScalarRows("i32", "f143c f1444"),
            NativeField("Node", "f1458"),
            NativeField("Node", "f16a8"),
            NativeField(
                "Array",
                "f1560",
                "i32",
                BodyValue=(
                    NativeField("Text", "file"),
                    NativeField(
                        "Array",
                        "rows",
                        "i32",
                        BodyValue=(
                            NativeField("Scalar", "key", "i32"),
                            NativeField("Node", "info"),
                            NativeField("Text", "name"),
                        ),
                        CountValue="n",
                    ),
                ),
                CountValue="n1568",
            ),
            NativeField(
                "Array",
                "f1570",
                "i32",
                BodyValue=(
                    NativeField("Text", "file"),
                    NativeField(
                        "Array",
                        "rows",
                        "i32",
                        BodyValue=(
                            NativeField("Text", "name"),
                            NativeField("Scalar", "key", "i32"),
                            NativeField("Node", "ref"),
                        ),
                        CountValue="n",
                    ),
                ),
                CountValue="n1578",
            ),
            NativeField("Scalar", "n1740", "i32"),
            NativeField("Embed", "f14f8", "moModelNameToXmlStreamNameMap_c"),
            NativeField("Embed", "zero_instance_blocks", "rf.suObList"),
            NativeField(
                "Array",
                "f1538",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n1538",
            ),
        ),
        "moModelNameToXmlStreamNameMap_c": (
            NativeField("Base", "su_CMapStringToString"),
            NativeField("Scalar", "f38", "i32"),
        ),
        "moDrwCompPropMgr_c": (
            NativeField("Node", "f18"),
            NativeField(
                "Array",
                "f08",
                "i32",
                BodyValue=(
                    NativeField("Node", "model"),
                    NativeField("Node", "properties"),
                ),
                CountValue="n10",
            ),
        ),
    }
)
