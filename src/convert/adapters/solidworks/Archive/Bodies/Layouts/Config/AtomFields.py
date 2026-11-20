from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# both archive conditions reach the same independent atom stamp fields
KAtomStampFields = (
    NativeField("Scalar", "f180", "i32"),
    NativeField("Scalar", "f188", "i32"),
    NativeField("Scalar", "f1b0", "i32"),
)

# standard embedded managers and their tagged atoms share one native field layout
KAtomFields = MappingProxyType(
    {
        "moAtomManager_c.FUN_4bcef8d0": (
            NativeField("Scalar", "f260", "i32"),
            NativeField("Length", "n6c", "i32", CountValue="atoms"),
            NativeField(
                "Repeat",
                "atoms",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n6c",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "fa8", "u32"),
        ),
        "moAtom_c": (
            NativeField("Base", "moNode_c.SerializeNode"),
            NativeField("Scalar", "f140", "i32"),
            NativeField("Normalize", "f144", "u32", ModeValue="AtomState"),
            NativeField("Scalar", "f130", "i32"),
            NativeField("Scalar", "f12c", "i32"),
            NativeField("Scalar", "f158", "u32"),
            NativeField("Scalar", "body_kind", "i32"),
            NativeField(
                "Branch",
                "body_kind",
                BodyValue=(NativeField("Fail", "atom body kind"),),
                ModeValue="Nonzero",
            ),
            NativeField("Scalar", "f170", "i32"),
            NativeField("Scalar", "f18c", "i32"),
            NativeField("Scalar", "f198", "i32"),
            NativeField(
                "Branch",
                "conditions",
                BodyValue=KAtomStampFields,
                OtherValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=KAtomStampFields,
                        ModeValue="Condition",
                        MaskValue=0x400000,
                    ),
                ),
                ModeValue="NotContext",
            ),
            NativeField("Scalar", "f19c", "i32"),
        ),
    }
)
