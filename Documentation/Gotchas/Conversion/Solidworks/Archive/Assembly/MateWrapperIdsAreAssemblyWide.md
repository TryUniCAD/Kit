# Mate wrapper IDs are allocated across the assembly

A first ordinary two-endpoint mate commonly has wrapper IDs zero and one.
Its endpoint ordinals are also zero and one. The fields coincide in this
case because the assembly's wrapper allocator starts empty.

The [disclosed native two-mate source](../../../../../../re/solidworks/measurements/2026/PublicCombinedMates01.json)
retains materialized wrapper IDs zero and one for its distance mate, then
two and three for its coincident mate. Each mate independently keeps local
endpoint ordinals zero and one. The Config-0 model stores next wrapper ID
four. Generated input follows the same allocation rule.

Validate `moPlaneRef_w.f74` against the owning mate ID and `f7c` against the
position in the mate's list. Read `f78` in the assembly allocation namespace,
bounded by Config-0 `moAssembly_c.fd48`, with no duplicate wrapper IDs
across the selected mates.
