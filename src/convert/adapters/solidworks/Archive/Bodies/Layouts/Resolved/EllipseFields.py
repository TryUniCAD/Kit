from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the measured ordinary ellipse body is embedded directly in its sketch member
KEllipseLayout = "sk.sgEllipse.FUN_4c586da0"

# the saved seam point uses a typed ellipse handle through the shared base serializer
KEllipseHandle = "sgEllipseHandle"

# the compact point ordinals retain the vendor field order without admitting wide alternate forms
KEllipseOrdinals = ("fdc_s", "fe0_s", "fe4_s", "fe8_s", "fec_s")


# compact ordinals preserve the observed wire widths and fail before a wide value can be replayed
def CompactOrdinals() -> tuple[NativeField, ...]:
    return tuple(
        RuleValue
        for FieldName in KEllipseOrdinals
        for RuleValue in (
            NativeField("Scalar", FieldName, "u16"),
            NativeField(
                "Branch",
                FieldName,
                ModeValue="Equals",
                MaskValue=65535,
                BodyValue=(NativeField("Fail", "wide SOLIDWORKS ellipse ordinal"),),
            ),
        )
    )


# the full positive rotation and local seam handle are the observed ordinary profile
KEllipseFields = MappingProxyType(
    {
        "moPartConfiguration_c.SerializeMBSMDataObjects": (
            NativeField(
                "Array",
                "fcd8",
                "u32",
                BodyValue=(NativeField("Fail", "populated SOLIDWORKS body mapping"),),
                CountValue="n",
            ),
        ),
        KEllipseHandle: (
            NativeField("Base", "sk.sgEntHandle.Serialize"),
            NativeField(
                "Branch",
                "idx",
                ModeValue="NotEquals",
                BodyValue=(NativeField("Fail", "alternate SOLIDWORKS ellipse handle"),),
            ),
        ),
        KEllipseLayout: (
            NativeField("Base", "sk.sgSegment.FUN_4c590920"),
            NativeField("Scalar", "fd8", "i32"),
            NativeField(
                "Branch",
                "fd8",
                ModeValue="NotEquals",
                MaskValue=1,
                BodyValue=(
                    NativeField("Fail", "alternate SOLIDWORKS ellipse rotation"),
                ),
            ),
            *CompactOrdinals(),
        ),
    }
)
