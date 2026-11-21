# Part default-context words select an actual command group

The ordinary part's `fb00/fb04` words are not independent display preferences, allocator counters or arbitrary reusable UI seeds. Native default-context methods own a context type, command group and separate unsaved runtime flags value.

Current store confirms the first two values through the actual part virtual hook before writing unsigned16 words. Current load confirms them again. The part hook changes an unconfirmed type to one and clears the group; an already confirmed type one preserves the group. Constructor `0/0` and saved `1/0` are distinct. Do not change prior default bytes merely to fit a saved profile.

The source `38284` value names the installed Features command group; the adjacent Drawing group is `38283`. The exact native resource/toolbar route supplies this vocabulary. It is not a per-source constant or a reason to emit localized caption text. `isEditingSelf` also controls document-owned versus edit-target delegation; do not confuse that virtual predicate with a document-kind query.

The new internal component accepts explicit Features/cleared group semantics for the confirmed ordinary part profile. Other groups and contexts refuse. Evidence: the [numeric source packet](../../../../../../re/solidworks/records/PartUiScalarConstruction2026.json), [field record](../../../../../../re/solidworks/records/ThroughAllUiScalars2026.md), and [host receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllUiScalars01.json). No new native acceptance is established.
