# the signed flag nibble follows the unsigned count
KGhostShift = 28

# the flags must not become part of the row count
KGhostCountMask = (1 << KGhostShift) - 1

# the signed high nibble can retain negative source flags
KGhostFlagMin = -8

# flags must fit the signed high nibble
KGhostFlagMax = 7

# sign extension is required for negative ghost flags
KGhostWordKind = "i32"
