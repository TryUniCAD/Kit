from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the resolved configuration section orders the model and part records using their native flags
KModelResRules = MappingProxyType(
    {
        "moModel_c.FUN_4c210610": (
            NativeField(
                "Array",
                "items",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Scalar", "value", "i32"),
                ),
                CountValue="n",
                ModeValue="Unsigned",
            ),
        ),
        "moModel_c.FUN_4c216d80": (
            NativeField("Embed", "f18", "su_CMapStringToOb.Serialize"),
            NativeField("Scalar", "f110", "i32"),
            NativeField("Scalar", "f114", "i32"),
        ),
        "moModel_c.FUN_4c22ec20": (
            NativeField("Scalar", "kind", "i32"),
            NativeField(
                "Branch",
                "kind",
                BodyValue=(NativeField("Base", "moModel_c.FUN_4c216d80"),),
                ModeValue="Equals",
                MaskValue=2,
            ),
        ),
        "moModel_c.FUN_4c234150": (
            NativeField("Base", "moConcept_c.SerializeResolvedData"),
            NativeField("Embed", "fd88", "moAtomManager_c.FUN_4bcef8d0"),
            NativeField("Embed", "fd90", "moGhostBodyIdManager_c.FUN_4bf050e0"),
            NativeField("Node", "f9d0"),
            NativeField("Embed", "fb08", "su_CObArray"),
            NativeField("Embed", "fae0", "moDetailDefs_c"),
            NativeField("Embed", "f9c8", "su_CObArray"),
            NativeField("Node", "f1e0"),
            NativeField("Node", "f9c0"),
            NativeField("Node", "f9d8"),
            NativeField(
                "Repeat",
                "f9f8",
                BodyValue=(NativeField("Node", "o"),),
                ModeValue="Fixed",
                MaskValue=10,
            ),
            NativeField("Normalize", "fd2c", "u8", ModeValue="Zero"),
            NativeField("Scalar", "fce8", "i32"),
            NativeField("Scalar", "fcec", "i32"),
            NativeField("Node", "fa88"),
            NativeField("Node", "attach"),
            NativeField("Normalize", "fd44", "i32", ModeValue="AtLeast", MaskValue=10),
            NativeField(
                "Present",
                "has_fdb8",
                "i32",
                BodyValue=(NativeField("Embed", "fdb8", "moNodeList_c.Serialize"),),
                CountValue="fdb8",
            ),
            NativeField("Normalize", "fd48", "i32", ModeValue="AtLeast"),
            NativeField("Node", "fe80"),
            NativeField("Node", "fa48"),
            NativeField("Scalar", "feb0", "i32"),
            NativeField("Scalar", "feb4", "i32"),
            NativeField(
                "Length", "nec8", "i32", CountValue="fec0", ModeValue="Positive"
            ),
            NativeField(
                "Repeat",
                "fec0",
                BodyValue=(NativeField("Scalar", "v", "u32"),),
                CountValue="nec8",
                ModeValue="Positive",
            ),
            NativeField("Node", "fa90"),
            NativeField("Scalar", "ff3c", "u32"),
            NativeField(
                "Length", "n1290", "i32", CountValue="f1288", ModeValue="Positive"
            ),
            NativeField(
                "Repeat",
                "f1288",
                BodyValue=(NativeField("Scalar", "v", "u32"),),
                CountValue="n1290",
                ModeValue="Positive",
            ),
            NativeField("Embed", "fb30", "su_CObArray"),
            NativeField("Embed", "fba8", "su_CObArray"),
            NativeField("Embed", "fb58", "su_CObArray"),
            NativeField("Embed", "fb80", "su_CObArray"),
            NativeField("Embed", "fbf8", "su_CObArray"),
            NativeField("Embed", "fbd0", "su_CObArray"),
            NativeField("Embed", "fc20", "su_CObArray"),
            NativeField("Embed", "fc70", "su_CObArray"),
            NativeField("Node", "fed0"),
            NativeField("Embed", "f240", "moForwardedFeatRefsList_c.FUN_4bb5ced0"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Node", "fe38"),),
                OtherValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Node", "fe38"),),
                        ModeValue="Condition",
                        MaskValue=4194304,
                    ),
                ),
                ModeValue="NotCondition",
                MaskValue=128,
            ),
            NativeField("Scalar", "f1010", "i32"),
            NativeField(
                "Length", "nff4", "i32", CountValue="ffe0", ModeValue="Positive"
            ),
            NativeField(
                "Repeat",
                "ffe0",
                BodyValue=(
                    NativeField("Node", "k"),
                    NativeField("Boolean", "v", "i32"),
                ),
                CountValue="nff4",
                ModeValue="Positive",
            ),
            NativeField(
                "Branch",
                "moPart_c",
                BodyValue=(
                    NativeField("Scalar", "f1014", "i32"),
                    NativeField(
                        "Branch",
                        "f1014",
                        BodyValue=(
                            NativeField("DirectNode", "f1018", "moSheetMetalMaster_c"),
                        ),
                        ModeValue="NotEquals",
                    ),
                ),
                ModeValue="Class",
            ),
            NativeField(
                "Length", "n10c4", "i32", CountValue="f10b0", ModeValue="Positive"
            ),
            NativeField(
                "Branch",
                "n10c4",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "f2c",
                        BodyValue=(
                            NativeField(
                                "Fail",
                                "FUN_4c234150 0x10b0 map without node flag 0x100",
                            ),
                        ),
                        ModeValue="BitsEqual",
                        MaskValue=256,
                    ),
                ),
                ModeValue="Greater",
            ),
            NativeField(
                "Repeat",
                "f10b0",
                BodyValue=(
                    NativeField("Scalar", "hi", "i32"),
                    NativeField("Scalar", "lo", "i32"),
                    NativeField("Scalar", "a", "i32"),
                    NativeField("Scalar", "b", "i32"),
                ),
                CountValue="n10c4",
                ModeValue="Positive",
            ),
            NativeField(
                "Branch",
                "moPart_c",
                BodyValue=(
                    NativeField("Scalar", "f1104", "i32"),
                    NativeField(
                        "Length",
                        "n1118",
                        "i32",
                        CountValue="f1108",
                        ModeValue="Positive",
                    ),
                    NativeField(
                        "Repeat",
                        "f1108",
                        BodyValue=(
                            NativeField("Embed", "o", "moDimIncrementId_c.Serialize"),
                        ),
                        CountValue="n1118",
                        ModeValue="Positive",
                    ),
                    NativeField("Scalar", "f1128", "i32"),
                    NativeField(
                        "Length",
                        "n1140",
                        "i32",
                        CountValue="f1130",
                        ModeValue="Positive",
                    ),
                    NativeField(
                        "Repeat",
                        "f1130",
                        BodyValue=(
                            NativeField("Embed", "o", "moDimIncrementId_c.Serialize"),
                        ),
                        CountValue="n1140",
                        ModeValue="Positive",
                    ),
                ),
                ModeValue="Class",
            ),
            NativeField("Scalar", "fb00", "i32"),
            NativeField("Scalar", "fd54", "i32"),
            NativeField(
                "Present",
                "has_f1270",
                "i32",
                BodyValue=(
                    NativeField("Embed", "f1270", "mo3DPrintSettings_c.FUN_4b541b90"),
                ),
                CountValue="f1270",
            ),
            NativeField("Node", "fa50"),
            NativeField("Scalar", "feb8", "i32"),
            NativeField("Text", "f760"),
            NativeField("Text", "f768"),
            NativeField("Node", "f12d0"),
            NativeField("Node", "f1338"),
            NativeField(
                "Length", "n1d8", "i32", CountValue="f1d0", ModeValue="Positive"
            ),
            NativeField(
                "Repeat",
                "f1d0",
                BodyValue=(
                    NativeField("Text", "k0"),
                    NativeField("Text", "k1"),
                    NativeField(
                        "Length", "m", "i32", CountValue="pairs", ModeValue="Positive"
                    ),
                    NativeField(
                        "Repeat",
                        "pairs",
                        BodyValue=(
                            NativeField("Scalar", "a", "i32"),
                            NativeField("Scalar", "b", "i32"),
                        ),
                        CountValue="m",
                        ModeValue="Positive",
                    ),
                ),
                CountValue="n1d8",
                ModeValue="Positive",
            ),
        ),
    }
)
