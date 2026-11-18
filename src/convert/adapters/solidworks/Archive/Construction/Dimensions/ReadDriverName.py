from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# stored parameter labels must remain a single name before the native owner suffix
def ReadDriverName(ValueInput: object) -> str:
    NameValue = ReadStyleText(ValueInput, "driving parameter name")
    if (
        not NameValue.strip()
        or "@" in NameValue
        or any(Value in NameValue for Value in ("\r", "\n", "\t"))
    ):
        raise ValueError("driving parameter name must identify one native label")
    return NameValue
