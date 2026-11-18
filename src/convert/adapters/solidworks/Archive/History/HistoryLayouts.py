from types import MappingProxyType
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Header.HeaderFields import KStampFields

# ordinary fresh history owns current version states and only empty biography data without silently admitting legacy or populated records
KHistoryLayouts = MappingProxyType(
    {
        "moStamp_c": tuple(
            (
                NativeField("Text", NameValue)
                if WireName == "text"
                else NativeField(
                    "Scalar", NameValue, {"H": "u16", "I": "u32"}[WireName]
                )
            )
            for NameValue, WireName in KStampFields
        ),
        "moBiography_c": (
            NativeField(
                "Array",
                "records",
                "i32",
                CountValue="n",
                ModeValue="Positive",
                BodyValue=(
                    NativeField(
                        "Fail", "populated biography is outside fresh history admission"
                    ),
                ),
            ),
        ),
        "moDateCodeState_c": (NativeField("Scalar", "f08", "i32"),),
        "moDateCodeHistory_c": (
            NativeField(
                "Array",
                "states",
                "i32",
                CountValue="n",
                ModeValue="Positive",
                BodyValue=(NativeField("Embed", "st", "moDateCodeState_c"),),
            ),
        ),
        "moVersionState_c": (
            NativeField("Embed", "f08", "moStamp_c"),
            NativeField("Scalar", "f30", "u32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "history state requires ordinary version 19000"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "f30")),
                    ("literal", 19000),
                ),
            ),
            NativeField("Node", "f38", "moDateCodeHistory_c"),
        ),
        "moVersionHistory_c": (
            NativeField(
                "Array",
                "states",
                "i32",
                CountValue="n",
                ModeValue="Positive",
                BodyValue=(NativeField("Embed", "st", "moVersionState_c"),),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "ordinary history requires at least one version state"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("LtE",),
                    ("lookup", ("scope",), ("literal", "n")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f2c", "u32"),
            NativeField("Scalar", "f30", "i32"),
            NativeField("Scalar", "f38", "u16"),
            NativeField("Scalar", "f3c", "i32"),
            NativeField("Scalar", "f40", "i32"),
        ),
    }
)

# compiled runtime metadata establishes schema one independently from the default chosen by an object helper
KHistorySchemas = MappingProxyType(
    {"moBiography_c": (1,), "moDateCodeHistory_c": (1,), "moVersionHistory_c": (1,)}
)
