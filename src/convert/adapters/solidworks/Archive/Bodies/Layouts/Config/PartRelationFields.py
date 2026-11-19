from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KRefWrapperTailFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# relation element coordinates and kind share one serializer across tokens and references
KRelationElementFields = (
    NativeField("Text", "f08"),
    NativeField("Scalar", "f10", "i32"),
    NativeField("Scalar", "f14", "i32"),
    NativeField("Scalar", "f18", "i32"),
    NativeField("Scalar", "f1c", "i32"),
)

# current part relations preserve the two expression sides and their original dimension handles
KPartRelationFields = MappingProxyType(
    {
        "moRelation_c": (
            NativeField("Text", "f10"),
            NativeField("Scalar", "f18", "u16"),
            NativeField("Scalar", "f48", "i32"),
            NativeField("Node", "f58", "moRelEquationSide_c"),
            NativeField("Node", "f60", "moRelEquationSide_c"),
            NativeField("Scalar", "f74", "i32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField("Text", "f38"),
            NativeField("Scalar", "f88", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Scalar", "f8c", "i32"),
        ),
        "moRelEquationSide_c": (
            NativeField("Embed", "f10", "suObList"),
            NativeField("Text", "f50"),
            NativeField("Scalar", "f58", "i32"),
            NativeField("Scalar", "f98", "i32"),
            NativeField("Node", "fa0", "moRelation_c"),
        ),
        "moRelDimension_c": (
            NativeField("Embed", "f30", "suObList"),
            NativeField("Node", "f78", "moCompRef_c"),
            NativeField("Node", "f80", "moDimRefWrapper_c"),
            *KRelationElementFields,
        ),
        "moRelOperator_c": KRelationElementFields,
        "moRelValue_c": KRelationElementFields,
        "moDimRefWrapper_c": (
            NativeField("Scalar", "fb0", "f64"),
            NativeField("Node", "f58"),
            *KRefWrapperTailFields,
        ),
    }
)
