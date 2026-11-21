from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Header.HeaderFields import KStampFields
from convert.adapters.solidworks.Archive.History.BioLayouts import KBiographyLayouts
from convert.adapters.solidworks.Archive.History.HistoryTypes import (
    KDateHistClass,
    KHistoryRootTypes,
    KVersionHistClass,
)

# history stamps share the independent header stamp field order and wire widths
KHistStampFields = tuple(
    (
        NativeField("Text", FieldName)
        if WireName == "text"
        else NativeField("Scalar", FieldName, {"H": "u16", "I": "u32"}[WireName])
    )
    for FieldName, WireName in KStampFields
)

# version state framing depends on its own stored file version before the date link
KVersionFields = (
    NativeField("Embed", "f08", "moStamp_c"),
    NativeField("Scalar", "f30", "u32"),
    NativeField(
        "Branch",
        "f30",
        BodyValue=(NativeField("Fail", "history state requires version 19000"),),
        ModeValue="NotEquals",
        MaskValue=19000,
    ),
    NativeField("Node", "f38", KDateHistClass.NameValue),
)

# each history count has a nonempty range because the native loader uses its final entry
KHistoryLayouts = MappingProxyType(
    {
        **KBiographyLayouts,
        "moStamp_c": KHistStampFields,
        "moDateCodeState_c": (NativeField("Scalar", "f08", "i32"),),
        KDateHistClass.NameValue: (
            NativeField(
                "Array",
                "states",
                "i32",
                CountValue="n",
                BodyValue=(NativeField("Embed", "st", "moDateCodeState_c"),),
            ),
            NativeField(
                "Branch",
                "n",
                OtherValue=(NativeField("Fail", "date code history requires states"),),
                ModeValue="Nonzero",
            ),
        ),
        "moVersionState_c": KVersionFields,
        KVersionHistClass.NameValue: (
            NativeField(
                "Array",
                "states",
                "i32",
                CountValue="n",
                BodyValue=(NativeField("Embed", "st", "moVersionState_c"),),
            ),
            NativeField(
                "Branch",
                "n",
                OtherValue=(NativeField("Fail", "version history requires states"),),
                ModeValue="Nonzero",
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

# runtime descriptors establish exact schema numbers for the three tagged owners
KHistorySchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (*KHistoryRootTypes, KDateHistClass)
    }
)
