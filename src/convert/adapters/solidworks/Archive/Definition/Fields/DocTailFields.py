from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# the common document trailer owns current options before each document kind stores its fields
KDocTailFields: tuple[NativeField, ...] = (
    NativeField("Text", "f1138"),
    NativeField("Embed", "f1158", "suObList"),
    NativeField("Text", "f1150"),
    NativeField("Embed", "ff40", "suObList"),
    NativeField("Text", "f1140"),
    NativeField("Embed", "ff88", "su_CStringArray"),
    NativeField("Embed", "ffb0", "su_CStringArray"),
    *MakeScalarRows("i32", "f1348 f1350 f134c f1354 fa78 f1358"),
    NativeField("Embed", "f1370", "PVDocSpecificOptionsData_c.Serialize"),
    *MakeScalarRows("i32", "f1388 f1390 f7bc f135c f13c8"),
    NativeField("Embed", "f13d0", "su_CDWordArray"),
    *MakeScalarRows("i32", "f1400 f1408 f13f0 fa7c fa80 fd78"),
    NativeField("Node", "f12e8"),
    *MakeScalarRows("i32", "f1424 f930 f1304 fd7c f1368 f3e8"),
    NativeField(
        "Array",
        "f11a0",
        "i32",
        BodyValue=(NativeField("Node", "o"),),
        CountValue="nvar",
    ),
)
