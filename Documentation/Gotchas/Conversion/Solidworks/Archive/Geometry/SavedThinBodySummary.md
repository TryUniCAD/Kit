# Saved thin body wrappers do not supply a topology summary

A saved thin-revolve part can retain its physical B-rep during explicit partial inspection while its separate portable body topology summary remains empty. Do not infer native solid count or mass properties from the number of body wrappers.

The four retained build-34.4.1.1011 native saves each return a global B-rep with one body, one shell, six faces, twelve edges and eight vertices. Their portable body summaries still contain zero solids and no volume. Their editable wall history is unverified, so strict full and design-only reads correctly refuse them.

Inspect the retained global B-rep and raw payloads when partial inspection is requested. Use revision-bound native measurements for qualified physical properties. Do not describe a wrapper count, non-null B-rep or passing refusal test as completed portable geometry or parametric acceptance. [Shared-suite evidence](../../../../../Changes/Solidworks/Inspection/Parts/SavedThinGuardSuite.md) and its exact native fixture manifest retain the observations.
