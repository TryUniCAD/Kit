from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# note owners are proved only for the ordinary drawing context including its inherited view bit
KNoteGate = (
    "And",
    (
        "compare",
        ("Eq",),
        ("lookup_or", ("context",), ("literal", "owner_is_drawing"), ("literal", 0)),
        ("literal", 1),
    ),
    (
        "compare",
        ("Eq",),
        (
            "BitOr",
            (
                "BitOr",
                (
                    "BitAnd",
                    (
                        "lookup_or",
                        ("context",),
                        ("literal", "conditions"),
                        ("literal", 0),
                    ),
                    ("literal", -65),
                ),
                ("lookup_or", ("context",), ("literal", "ctx874"), ("literal", 0)),
            ),
            ("lookup_or", ("context",), ("literal", "ctx894"), ("literal", 0)),
        ),
        ("literal", 0),
    ),
)


# inherited note helpers must fail before consuming an unproved alternate context
def GateNote(FieldsValue: tuple[NativeField, ...]) -> tuple[NativeField, ...]:
    return (
        NativeField(
            "Branch",
            "",
            BodyValue=FieldsValue,
            OtherValue=(NativeField("Fail", "drawing note alternate archive context"),),
            ModeValue="Expression",
            ExpressionValue=KNoteGate,
        ),
    )
