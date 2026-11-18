from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# ordinary drawing references retain their native temporary view bit while all special frdata contexts remain outside the proved profile
KCompMode = (
    "compare",
    ("Eq",),
    (
        "BitOr",
        (
            "BitOr",
            (
                "BitAnd",
                ("lookup_or", ("context",), ("literal", "conditions"), ("literal", 0)),
                ("literal", ~0x40),
            ),
            ("lookup_or", ("context",), ("literal", "ctx874"), ("literal", 0)),
        ),
        ("lookup_or", ("context",), ("literal", "ctx894"), ("literal", 0)),
    ),
    ("literal", 0),
)

# the concrete profile extension belongs only to the existing drawing archive context rather than general resolved model admission
KCompGate = (
    "select",
    (
        "compare",
        ("Eq",),
        ("lookup_or", ("context",), ("literal", "owner_is_drawing"), ("literal", 0)),
        ("literal", 1),
    ),
    KCompMode,
    ("literal", False),
)

# the native component profile serializer contributes only its independently proved existing component feature base
KCompFields = MappingProxyType(
    {
        "moCompProfile_c": (
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Base", "moCompFeature_c"),),
                OtherValue=(
                    NativeField(
                        "Fail", "component profile special FRData archive context"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=KCompGate,
            ),
        ),
    }
)
