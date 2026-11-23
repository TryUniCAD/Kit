from struct import Struct

# the measured Windows database uses three equal physical pages
KUnqlitePageSize = 4096

# the pager header identifies the engine before the bucket map can be interpreted
KUnqlitePager = Struct(">7sIIIIH")

# the linear header includes its single logical-to-physical bucket mapping
KUnqliteMap = Struct(">IIQQQQIQQ")

# the bucket links occupied records and reusable space independently
KUnqliteBucket = Struct(">HHQ")

# each local cell owns its key hash payload sizes and successor references
KUnqliteCell = Struct(">IIQHQ")

# free blocks retain their own link and total extent outside the live records
KUnqliteFree = Struct(">HH")
