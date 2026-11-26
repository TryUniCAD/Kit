from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# reader and writer share this boundary so the native class identity stays aligned
KDefPrefixFields = MakeScalarRows("i32", "fa58 fa5c fa60 fa64 fa74")
