from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KRecordFields = MappingProxyType(
    {
        "moPMarkRecord_c": (NativeField("Scalar", "f18", "i32"),),
    }
)
