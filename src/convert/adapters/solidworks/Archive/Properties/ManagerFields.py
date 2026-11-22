from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# each keyed owner stores its own native integer key before the concrete object
KPropKeyRows = (NativeField("Scalar", "key", "i32"), NativeField("Node", "o"))

# compatible and empty advanced managers share this structural field grammar
KManagerFields = MappingProxyType(
    {
        "moCusPropMgr_c": (
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField(
                "Array", "f20", "u32", CountValue="n20", BodyValue=KPropKeyRows
            ),
            NativeField("Scalar", "f54", "u8"),
        ),
        "moCusPropContainer_c": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10"),
            NativeField("Node", "f18"),
            NativeField("Scalar", "f20", "i32"),
        ),
        "moFilePropContainer_c": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10"),
        ),
        "moCutListPropContainer_c": (
            NativeField(
                "Array", "f08", "u32", CountValue="n08", BodyValue=KPropKeyRows
            ),
            NativeField(
                "Array", "f38", "u32", CountValue="n38", BodyValue=KPropKeyRows
            ),
        ),
    }
)

# the measured concrete property owners use their individual schema one descriptors
KManagerSchemas = MappingProxyType({ClassName: (1,) for ClassName in KManagerFields})
