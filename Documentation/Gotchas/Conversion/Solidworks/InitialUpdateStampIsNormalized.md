# Initial update stamps change during native loading

The header constructor seeds its update and body counters with `101`.
That does not mean both counters retain that value after native loading.

The 2026 header serializer changes a loaded update stamp of `101` to `102`
for file versions above `150`. The body counter has no corresponding fixup
in that serializer. At version `19000`, the later stored timestamp read also
overwrites the temporary current-time assignment made by the update fixup.

Keep wire values separate from native in-memory state. A byte-identical
codec round trip does not exercise this fixup. Do not replace the constructor
seed or infer a feature-count formula without the actual lifecycle rule.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md#header-counter-and-save-lifecycle)
records the target module hash, instruction addresses and REA evidence.
Generated-header native acceptance remains unfinished.
