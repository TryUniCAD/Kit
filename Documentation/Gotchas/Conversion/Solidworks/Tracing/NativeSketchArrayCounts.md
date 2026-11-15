# Native sketch arrays and endpoint identity

API point-list length and equal coordinates do not independently prove how
native line endpoints share point slots. Point identities from `GetID` are
local to the owning sketch and element type, not persistent references.

On the exact 2026 model image, `sgSketch::getActivePointCount` at `0x4c4b0a60`
reads the array at sketch `+8`, its data pointer at array `+8`, and the raw count
through `amDynamicArrayCount`. That helper at `sldmgu!0x31deec50` reads signed
32 bits at data `-0x10`. A null data pointer means zero; a null array is not a
proved empty array. Point stride is `0x158`; bit zero at point `+0x54` marks
deleted entries. Point type at `+0xe4` is a 32-bit field, not a 16-bit field.

`getMaxLineCount` at `0x4c4b3fa0` follows sketch `+0x10` through the same array
layout. Line stride is `0xf0`. Generic `isDeleted` at `0x4c5cdd70` proves the
same deletion bit. The native start/end helpers at `0x4c492260` and `0x4c4921f0`
read signed point indices at line `+0xc8` and `+0xcc`, respectively. Count unique
valid endpoint indices across nondeleted lines within one sketch; do not merge
slots merely because their coordinates match.

The observer retains array identities, bounded-scan completeness and raw flags.
Its first successful authoring capture recorded point counts and API endpoint
identities, before line-index snapshots were added. Do not retroactively claim
those later fields were captured. Zero-count snapshots from that older observer
did not distinguish null arrays, so they do not prove an empty native array.
