# assembly output admits only ordinary write policy plus its explicit linked native destination without a source file resolver
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
    }
)
