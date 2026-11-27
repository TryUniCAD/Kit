from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# both directions refuse skipped model sections rather than treating them as sized bodies
KSectSkipMask = 0x180000

# the size prefix excludes its own unsigned word
KSectLength = KScalarWords["u32"]
