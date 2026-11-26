from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# compact field vocabulary keeps recovered schemas reviewable without recorded payloads
def ShapeFields(ShapeText: str) -> tuple[XmtField, ...]:
    FieldValues: list[XmtField] = []
    for TokenValue in ShapeText.split():
        NameValue, Encoding = TokenValue.split(":")
        Encoding, _, CountText = Encoding.partition("*")
        PointerClass = int(Encoding[1:]) if Encoding.startswith("p") else 0
        FieldValues.append(
            XmtField(
                NameValue,
                "p" if PointerClass else Encoding,
                PointerClass,
                int(CountText or 0),
            )
        )
    return tuple(FieldValues)
