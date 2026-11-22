from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import KPartMeasureOpt

# assembly options carry native proof and the logical locator separately from ordinary write policy
KAsmOptionNames = frozenset(
    {
        "final_destination",
        "final_overwrite",
        "allow_carrier",
        "require_self_contained",
        "require_native_transfers",
        "allow_non_native",
        "portable",
        "native_destination",
        KPartMeasureOpt,
    }
)
