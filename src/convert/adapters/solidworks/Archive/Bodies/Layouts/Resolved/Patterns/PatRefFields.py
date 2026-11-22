from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternDatumFields import (
    KPatternDatumFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# point and dimension wrappers share the actual owner and optional reference transforms
KRefWrapperTransforms = (
    NativeField("Scalar", "f68", "u16"),
    NativeField("Node", "f60", "moComponent_c"),
    NativeField("Scalar", "f6c", "i32"),
    NativeField("Scalar", "f08", "i32"),
    NativeField("Scalar", "has_f10", "u16"),
    NativeField(
        "Branch",
        "has_f10",
        BodyValue=(NativeField("Embed", "f10", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "has_f18", "u16"),
    NativeField(
        "Branch",
        "has_f18",
        BodyValue=(NativeField("Embed", "f18", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
)

# the native wrapper stores its reference words immediately after the transform fields
KRefWrapperTailFields = (
    *KRefWrapperTransforms,
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f20", "i32"),
    NativeField("Scalar", "f74", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f50", "i32"),
    NativeField("Scalar", "f70", "i32"),
    NativeField("Scalar", "f34", "i32"),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f98", "i32"),
    NativeField("Scalar", "f38", "i32"),
)


# the single local pattern has a hinge axis or a selected direction plane
KRefWrapperHead = NativeField(
    "Branch",
    "pattern_datum",
    BodyValue=KPatternDatumFields,
    OtherValue=(
        NativeField("Fail", "local pattern reference has no owned datum context"),
    ),
    ModeValue="Context",
)


# line and curve wrapper bodies share the ordinary finite range and local frame
KPatRefFields = MappingProxyType(
    {
        "moRefWrapper_c": (
            NativeField(
                "Branch",
                "constraint_hinge",
                BodyValue=(NativeField("Node", "f58", "moCompRefAxis_c"),),
                OtherValue=(KRefWrapperHead,),
                ModeValue="Context",
            ),
            *KRefWrapperTailFields,
        ),
        "moCurveRef_w": (
            NativeField("Base", "moRefWrapper_c"),
            NativeField("Scalar", "fb0", "f64"),
            NativeField("Scalar", "fb8", "f64"),
        ),
        "moLineRef_w": (
            NativeField("Base", "moCurveRef_w"),
            NativeField("Embed", "fc8", "mgPoint_c.restore"),
            NativeField("Embed", "fe0", "mgVector_c.restore"),
            NativeField("Scalar", "ff8", "u8"),
        ),
    }
)
