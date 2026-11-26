from convert.adapters.solidworks.Archive.Partition.FieldHeader import FieldHeader
from convert.adapters.solidworks.Archive.Partition.XmtShape import XmtShape


# first use schema checks must follow the native field edit grammar for this build
def SchemaHeader(ShapeValue: XmtShape) -> bytes:
    BaseFields = ShapeValue.BaseValue
    FieldsValue = ShapeValue.FieldsValue
    if BaseFields == FieldsValue:
        return bytes((255,))
    HeaderValue = bytearray((len(FieldsValue),))
    BaseIndex = CurrentIndex = 0
    while BaseIndex < len(BaseFields) and CurrentIndex < len(FieldsValue):
        BaseField = BaseFields[BaseIndex]
        CurrentField = FieldsValue[CurrentIndex]
        if BaseField == CurrentField:
            HeaderValue.extend(b"C")
            BaseIndex += 1
            CurrentIndex += 1
        elif BaseField in FieldsValue[CurrentIndex:]:
            HeaderValue.extend(b"I" + FieldHeader(CurrentField))
            CurrentIndex += 1
        else:
            HeaderValue.extend(b"D")
            BaseIndex += 1
    for FieldValue in FieldsValue[CurrentIndex:]:
        HeaderValue.extend(b"A" + FieldHeader(FieldValue))
    HeaderValue.extend(b"Z")
    return bytes(HeaderValue)
