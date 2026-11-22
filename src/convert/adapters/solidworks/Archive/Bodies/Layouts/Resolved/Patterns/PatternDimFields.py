from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# count parameters keep their signed scalar separate from the inherited binary64 display cache
KPatternDimFields = MappingProxyType(
    {
        "moDisplayDim_c": (NativeField("Base", "moDisplayDim_c.FUN_4c82c3d0"),),
        "moNumberDim_c": (NativeField("Base", "moFeatureDim_c.FUN_4c833f00"),),
        "moIntegerParameter_c": (
            NativeField("Base", "dm.moParameter_c.FUN_4c17a330"),
            NativeField("Scalar", "f58", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "f60", "u8"),
                    NativeField(
                        "Branch",
                        "f60",
                        BodyValue=(NativeField("Scalar", "f5c", "i32"),),
                        ModeValue="Nonzero",
                    ),
                ),
                MaskValue=0x80,
                ModeValue="NotCondition",
            ),
        ),
    }
)
