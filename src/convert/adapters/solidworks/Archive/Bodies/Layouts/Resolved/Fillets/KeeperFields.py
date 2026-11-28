from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# keeper surface rows share the existing entity id framing while retaining concrete surface types
KKeeperFields = MappingProxyType(
    {
        "moFilletSIdKeeper_c": (
            NativeField("Embed", "f18", "mo_dynSurfIdArr.Serialize"),
            NativeField("Embed", "ff0", "rf.suObArray"),
        ),
        "mo_dynSurfIdArr.Serialize": (
            NativeField("Scalar", "n", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "fillet keeper count"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotIn",),
                    ("lookup", ("scope",), ("literal", "n")),
                    ("sequence", (("literal", 0), ("literal", 2))),
                ),
            ),
            NativeField(
                "Repeat",
                "items",
                BodyValue=(NativeField("Embed", "id", "moEntityId_c"),),
                CountValue="n",
            ),
        ),
        "moFilletSurfIdRep_c": (NativeField("Base", "er.FUN_4bbaa6a0"),),
        "moSurfaceIdRep_c": (NativeField("Base", "er.FUN_4bba8790"),),
    }
)
