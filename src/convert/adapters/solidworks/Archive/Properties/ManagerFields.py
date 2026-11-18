from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# compatible property managers have no keyed advanced owners and retain their complete native framing
KManagerFields = MappingProxyType(
    {
        "moCusPropMgr_c": (
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField(
                "Array",
                "f20",
                "u32",
                CountValue="n20",
                BodyValue=(NativeField("Fail", "populated advanced property manager"),),
            ),
            NativeField("Scalar", "f54", "u8"),
        ),
    }
)

# the compatible manager descriptor binds the observed current schema without admitting advanced subclasses
KManagerSchemas = MappingProxyType({"moCusPropMgr_c": (1,)})
