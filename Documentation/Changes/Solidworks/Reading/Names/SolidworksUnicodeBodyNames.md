# Preserve authored Unicode solid-body labels

The bounded SOLIDWORKS single-solid reader can preserve authored Unicode body labels from the actual archive atom and agreeing body-owned UTF-16 value. It retains the legacy character payload as bytes, including lossy compatibility text, and preserves exact B-rep payloads and unrelated document semantics. Existing ASCII naming behavior remains exact.

Use `open_document(..., source_format="solidworks.sldprt")` with geometry enabled. The profile requires complete atom, feature, kernel and B-rep ownership. The reader withholds the label when it encounters conflicting wide owners, unsupported alternate attributes or a corrupt cache.

Root's 56-worker process replay passed 23 groups and 115 paired mode comparisons, including all nine new native source states, four prior ASCII states and ten mismatch/compatibility fixtures. Public reads attempted zero extra file accesses. The source cohort separately passed eight native author/reopen processes with healthy controls. See [the measured reader record](../../../../../re/solidworks/records/SdkUnicodeBodyNames2026.md), [the process receipt](../../../../../re/solidworks/measurements/2026/SdkUnicodeBodyReaderProcess01.json) and [the lossy-character gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/PartNames/LegacyCharacterBodyNameCanBeLossy.md).

Named-body writing and original held-out acceptance remain open.
