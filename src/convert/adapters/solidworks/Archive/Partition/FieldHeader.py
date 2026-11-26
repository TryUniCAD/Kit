from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# schema descriptors are computed from declared field knowledge rather than captured headers
def FieldHeader(FieldValue: XmtField) -> bytes:
    NameBytes = FieldValue.NameValue.encode("ascii")
    HeaderValue = bytes((len(NameBytes),)) + NameBytes
    HeaderValue += PackValue(">Hh", FieldValue.PointerClass, FieldValue.CountValue + 1)
    if not FieldValue.PointerClass:
        Encoding = FieldValue.EncodingValue.encode("ascii")
        HeaderValue += bytes((len(Encoding),)) + Encoding
    if FieldValue.CountValue == 1:
        HeaderValue += bytes((1,))
    return HeaderValue
