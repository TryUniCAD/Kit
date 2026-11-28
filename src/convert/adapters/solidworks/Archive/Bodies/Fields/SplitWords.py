from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# both halves of a split count have the same unsigned width
KSplitWordKind = "u32"

# the most significant count half precedes the least significant half
KSplitShift = KScalarWords[KSplitWordKind].size * 8

# each retained half must fit the unsigned wire domain
KSplitWordMax = (1 << KSplitShift) - 1
