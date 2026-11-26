from struct import Struct
from types import MappingProxyType

# primitive vocabulary binds native signedness and width independently from field values
KScalarWords = MappingProxyType(
    {
        "u8": Struct("<B"),
        "i8": Struct("<b"),
        "u16": Struct("<H"),
        "i16": Struct("<h"),
        "u32": Struct("<I"),
        "i32": Struct("<i"),
        "u64": Struct("<Q"),
        "i64": Struct("<q"),
        "f32": Struct("<f"),
        "f64": Struct("<d"),
    }
)
