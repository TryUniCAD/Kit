from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the ordinary part root defines the two sequential bounded archive bodies
KPartRootRules = MappingProxyType(
    {
        "moPart_c": (
            NativeField("Base", "moPart_c.FUN_4c2309d0"),
            NativeField("Base", "moPart_c.FUN_4c2378b0"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "moDownstreamIdData_c under condition 0x80"),
                ),
                ModeValue="Condition",
                MaskValue=128,
            ),
        ),
        "moPart_c.FUN_4c2309d0": (
            NativeField(
                "Section",
                "",
                BodyValue=(
                    NativeField("Base", "moModel_c.FUN_4c22ec80"),
                    NativeField("Node", "f1418"),
                    NativeField("Node", "f1420"),
                    NativeField("Node", "f1588"),
                    NativeField("Embed", "f938", "moBodyVizProps_c.FUN_4c240300"),
                    NativeField("Scalar", "f15f0", "i32"),
                    NativeField("Scalar", "f1614", "i32"),
                    NativeField("Scalar", "f1618", "i32"),
                    NativeField("Scalar", "f161c", "i32"),
                    NativeField("Embed", "f1c70", "moModel_c.FUN_4c210610"),
                ),
                MaskValue=1,
            ),
        ),
        "moPart_c.FUN_4c2378b0": (
            NativeField(
                "Section",
                "",
                BodyValue=(
                    NativeField("Base", "moModel_c.FUN_4c234150"),
                    NativeField("Scalar", "f14f8", "i32"),
                    NativeField("Scalar", "f1428", "u8"),
                    NativeField("Scalar", "f14d8", "i32"),
                    NativeField("Normalize", "f152c", "i32", ModeValue="Identity"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Branch",
                                "",
                                BodyValue=(
                                    NativeField(
                                        "Branch",
                                        "",
                                        BodyValue=(
                                            NativeField(
                                                "MassCaches", "f1628", OtherName="f1638"
                                            ),
                                        ),
                                        ModeValue="NotCondition",
                                        MaskValue=2147483648,
                                    ),
                                ),
                                ModeValue="NotCondition",
                                MaskValue=1,
                            ),
                        ),
                        ModeValue="NotCondition",
                        MaskValue=128,
                    ),
                    NativeField("Scalar", "f1400", "i32"),
                    NativeField("Node", "f13f8"),
                    NativeField("Scalar", "f1698", "i32"),
                    NativeField("Scalar", "f169c", "i32"),
                    NativeField(
                        "Present",
                        "has_f16b8",
                        "i32",
                        BodyValue=(
                            NativeField("Length", "n16b8", "u32", CountValue="f16b8"),
                            NativeField(
                                "Repeat",
                                "f16b8",
                                BodyValue=(
                                    NativeField("Scalar", "k", "i32"),
                                    NativeField("Node", "o"),
                                ),
                                CountValue="n16b8",
                                ModeValue="Unsigned",
                            ),
                            NativeField("Length", "n16d0", "i32", CountValue="f16d0"),
                            NativeField(
                                "Repeat",
                                "f16d0",
                                BodyValue=(
                                    NativeField("Scalar", "k", "i32"),
                                    NativeField("Scalar", "v", "u8"),
                                ),
                                CountValue="n16d0",
                                ModeValue="Positive",
                            ),
                        ),
                        CountValue="f16b8",
                    ),
                    NativeField("Length", "n16f8", "i32", CountValue="f16e8"),
                    NativeField(
                        "Repeat",
                        "f16e8",
                        BodyValue=(NativeField("Node", "o"),),
                        CountValue="n16f8",
                    ),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Branch",
                                "",
                                BodyValue=(
                                    NativeField(
                                        "Branch",
                                        "f161c",
                                        BodyValue=(
                                            NativeField(
                                                "BBoxCache", "f1640", ModeValue="Tagged"
                                            ),
                                        ),
                                        ModeValue="Equals",
                                    ),
                                ),
                                ModeValue="NotCondition",
                                MaskValue=1,
                            ),
                        ),
                        ModeValue="NotCondition",
                        MaskValue=128,
                    ),
                    NativeField("Scalar", "f18d4", "i32"),
                    NativeField("Scalar", "f18d8", "u32"),
                    NativeField("Scalar", "f1900", "i32"),
                    NativeField("Scalar", "f1be0", "i32"),
                    NativeField(
                        "Branch",
                        "f1be0",
                        BodyValue=(
                            NativeField("Length", "n1b98", "i32", CountValue="f1bc8"),
                            NativeField(
                                "Repeat",
                                "f1bc8",
                                BodyValue=(NativeField("Scalar", "v", "i32"),),
                                CountValue="n1b98",
                                ModeValue="Positive",
                            ),
                        ),
                        ModeValue="NotEquals",
                    ),
                ),
                MaskValue=2,
            ),
        ),
    }
)
