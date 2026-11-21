from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the current native property serializer has nine typed fields with independently traced store order
KPropertyFields = MappingProxyType(
    {
        "moCustomProperty": (
            NativeField("Text", "f08"),
            NativeField("Text", "f10"),
            NativeField("Text", "f18"),
            NativeField("Scalar", "f2c", "i32"),
            NativeField("Scalar", "f28", "u32"),
            NativeField("Text", "f20"),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f3c", "i32"),
        ),
    }
)
