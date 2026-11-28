from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# small native collections use an unsigned short
KCountShort = KScalarWords["u16"]

# the native extension stores an unsigned long
KCountLong = KScalarWords["u32"]

# framework collections can extend beyond the native long domain
KCountWide = KScalarWords["u64"]

# the short marker announces a long count
KCountLongMark = 0xFFFF

# only framework counts treat this long value as an extension marker
KCountWideMark = 0xFFFFFFFF

# framework counts are limited by the unsigned wide word
KCountWideMax = 0xFFFFFFFFFFFFFFFF
