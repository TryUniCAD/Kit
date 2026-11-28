from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldText,
    RequireNode,
)


# shared header and archive body readers expose the same decoded string handle identity
def ReadFileText(HandleValue: object) -> str:
    Handle = RequireNode(HandleValue, "moCStringHandle_c")
    Fields = Handle.FieldsValue
    TextValues = tuple(
        FieldText(Fields, FieldName)
        for FieldName in ("text", "f08")
        if FieldName in Fields
    )
    if "value" in Fields:
        TypedValue = Fields["value"]
        if not isinstance(TypedValue, CStringValue) or not TypedValue.TextValue:
            raise ValueError(
                "native file handle requires a nonempty typed string value"
            )
        TextValues = (*TextValues, TypedValue.TextValue)
    if not TextValues or len(set(TextValues)) != 1:
        raise ValueError("native file handle text representations differ or are absent")
    return TextValues[0]
