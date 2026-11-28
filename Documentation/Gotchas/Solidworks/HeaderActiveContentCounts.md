# Header active-content counters do not count ordinary features

The adjacent integers `moHeader_c.f9c/fa0/fa4/fa8/fac/fb0` can look like a
feature-count mask and per-feature-family totals. The 2026 binary names the
mutator `addActiveContentFlag(swActiveContentTypes_e)`. Its recovered callers
classify macro features before adding flags 2, 4 or 8; ordinary sketches and
extrusions do not follow those caller branches.

In `sldarchiveu.dll`, `0x31a04a40` increments the matching counter for flags
2/4/8/16/32 and ORs the flag into the mask. Removal `0x31a05920` decrements
that counter and clears its mask bit only when the count becomes zero.
In `sldmodu.dll`, macro-feature handling in `moFeature_c::undelete`
(`0x4bb53b20`, add call `0x4bb53c31`) and `onDelete` (`0x4bb4e320`, remove
call `0x4bb4e420`) confirms the three-way macro classification.

Derive these fields from recovered active-content semantics, not visible feature
count. The native macro bit behind category 2, categories 16/32, the complete
mask domain and other possible subsystem contributors still need recovery.
Constructor-zero seeds remain an initial-profile research candidate and do not
establish final-save neutrality. See the
[construction evidence](../../../re/solidworks/records/MetadataConstruction2026.md#active-content-is-not-ordinary-feature-count)
for exact branch conditions and binary ownership.
