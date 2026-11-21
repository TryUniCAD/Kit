# The BOM getter can allocate an empty manager

Expectation: querying the document's BOM-manager pointer only reports existing data, and a saved manager means a populated BOM.

Actual behavior: the exact 2026 native `uiModelDoc_c::getBomInfoMgr_c` at `0x49785260` tests document `+0xab8`. If null, it allocates and constructs the empty manager, stores that pointer and returns it. Its independently owned list can remain genuinely empty. The pointer setter only stores the supplied pointer. This is confirmed static source behavior, not a new COM/runtime measurement.

Workaround: distinguish source wire presence from population and runtime queries. Read the actual typed archived pointer and validate the exact empty count/list. Construct an empty node explicitly when the source intent requires it; refuse populated children until their semantics are represented. Do not infer manager presence from unrelated UI words or seed saved rendering allocator state from a captured default.

[Exact native source rules](../../../../../../re/solidworks/records/EmptyModelManagerRules2026.json) · [Composition record](../../../../../../re/solidworks/records/ThroughAllEmptyManagers2026.md) · [Host receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllEmptyManagers01.json)
