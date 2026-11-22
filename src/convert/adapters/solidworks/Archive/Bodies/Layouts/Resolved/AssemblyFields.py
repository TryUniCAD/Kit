from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KAssemblyFields = MappingProxyType(
    {
        "moLiveSectionFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Normalize", "f378", "i32", ModeValue="Equals", MaskValue=1),
        ),
        "moMateGroup_c": (
            NativeField("Base", "moModelFeature_c"),
            NativeField(
                "Array",
                "discarded_manager_records",
                "i32",
                BodyValue=(NativeField("Fail", "moAemManager_c persisted entry"),),
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "f4e8",
                "Split",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                ModeValue="Combined",
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Scalar", "f4f8", "i32"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        (
                            "lookup_or",
                            ("context",),
                            ("literal", "conditions"),
                            ("literal", 0),
                        ),
                        ("literal", 128),
                    ),
                    ("literal", 0),
                ),
            ),
        ),
    }
)
