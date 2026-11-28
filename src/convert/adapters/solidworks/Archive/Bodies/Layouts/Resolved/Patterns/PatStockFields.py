from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the raised seed and terminal pattern use the actual inherited solid selector and ice feature
KPatStockFields = MappingProxyType(
    {
        "moCompSolidBody_c": (
            NativeField("Base", "moCompRef_c"),
            NativeField("Node", "ff0", "moFaceRef_c"),
            NativeField("Scalar", "n110", "i32"),
            NativeField(
                "Repeat",
                "f110",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                CountValue="n110",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "f108", "i32"),
            NativeField("Scalar", "f104", "i32"),
            NativeField("Scalar", "f100", "i32"),
        ),
        "moICE_c": (NativeField("Base", "moExtrusion_c"),),
    }
)
