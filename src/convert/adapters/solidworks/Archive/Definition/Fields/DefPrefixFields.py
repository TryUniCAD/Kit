from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# the current ui prefix stores the four tessellation preferences and native format switch
KDefPrefixFields = MakeScalarRows("i32", "fa58 fa5c fa60 fa64 fa74")
