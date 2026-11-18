from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# downstream references preserve wire row order and words before the native reader normalizes its maps and vectors
KDownstreamFields = MappingProxyType(
    {
        "moEntRefDownstreamIdData_c": (
            NativeField(
                "Array",
                "f10",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Scalar", "value", "i32"),
                ),
                CountValue="n10",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "f20",
                "i32",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                CountValue="n20",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f40_0", "i32"),
            NativeField("Scalar", "f40_1", "i32"),
        ),
    }
)
