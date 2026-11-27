from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# most graph references fit in an unsigned short
KTagShort = KScalarWords["u16"]

# large references carry a separate extended tag word
KTagLong = KScalarWords["u32"]

# the null tag does not refer to an allocated map entry
KTagNull = 0

# a new class tag introduces its descriptor
KTagNewClass = 0xFFFF

# the wide marker precedes the extended tag word
KTagWideMark = 0x7FFF

# the short tag uses its high bit to distinguish class references
KTagClassBit = 0x8000

# the long tag uses its high bit to distinguish class references
KTagWideClass = 0x80000000
