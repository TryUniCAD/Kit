from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# short strings carry a one byte length
KTextByte = KScalarWords["u8"]

# longer strings and wide text markers carry a second word
KTextWord = KScalarWords["u16"]

# the final length extension carries a long word
KTextLong = KScalarWords["u32"]

# the byte marker announces a following word
KTextWordMark = 0xFF

# the wide marker changes both the unit size and text encoding
KTextWideMark = 0xFFFE

# the word marker announces a following long value
KTextLongMark = 0xFFFF

# cstring lengths must fit a signed long
KTextLengthMax = 0x7FFFFFFF

# native wide text stores little endian code units
KWideEncoding = "utf-16-le"

# source text can carry isolated code units
KWideErrors = "surrogatepass"

# byte text needs lossless mapping for the full byte domain
KByteEncoding = "latin-1"

# wide strings count code units rather than bytes
KWideUnitBytes = 2
