from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the ordinary part suffix keeps physical density and embedded model data in separate records
KPartMatFields = MappingProxyType(
    {
        "gcXhatch_c": (
            NativeField("Text", "f08"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Scalar", "f18", "f64"),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f24", "i32"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f2c", "i32"),
            NativeField("Scalar", "f30", "i32"),
        ),
        "moMaterial_c": (NativeField("Node", "f08"),),
        "moParameter_c.FUN_4c17a330": (
            NativeField("Base", "moNode_c.SerializeLWData"),
            NativeField("Node", "f48"),
        ),
        "moDensityParameter_c": (
            NativeField("Base", "moParameter_c.FUN_4c17a330"),
            NativeField("Scalar", "f58", "f64"),
            NativeField("Scalar", "f68", "u8"),
            NativeField(
                "Branch",
                "f68",
                BodyValue=(NativeField("Fail", "alternate part density"),),
                ModeValue="Nonzero",
            ),
        ),
        "uoModelData_c": (
            NativeField("Node", "f08"),
            NativeField("Scalar", "f10", "i32"),
        ),
    }
)
