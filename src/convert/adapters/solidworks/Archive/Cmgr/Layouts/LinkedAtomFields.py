from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native configuration atom links retain creator and last modifier words separately
KLinkedAtomFields = (
    NativeField("Scalar", "f08", "i32"),
    NativeField("Embed", "f90", "su_CDWordArray"),
    NativeField("Embed", "fd0", "su_CDWordArray"),
    *(
        NativeField(
            "Array",
            FieldName,
            "u32",
            BodyValue=(NativeField("Fail", "alternate linked atom map"),),
            CountValue=CountName,
        )
        for FieldName, CountName in (
            ("ff0", "nf0"),
            ("f100", "n100"),
            ("f110", "n110"),
            ("f120", "n120"),
        )
    ),
)
