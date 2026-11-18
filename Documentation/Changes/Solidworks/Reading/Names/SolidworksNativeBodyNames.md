# Native single-solid body names

Strict SOLIDWORKS part reading can project a proven body's actual native label and bind its complete B-rep to the existing design-body identity. The projection requires a coherent version-19000 active partition, registered attributes, actual manager/feature output atom and full topology. It preserves the original geometry and payloads.

The current boundary is the disclosed ordinary modern single-solid profile with a printable ASCII implicit label, or agreeing explicit archive and kernel labels. Unsupported or ambiguous owners keep their existing reader behavior. History-only reads, old releases, multiple bodies, conflicting/alternate labels and no-cache named atoms are not newly qualified. No named-body writer is enabled.

Use the existing `open_document(..., source_format="solidworks.sldprt")` route. No new public option is required. A successful binding records narrowly scoped native-body provenance and ownership metadata; it is not a format-wide acceptance claim.

The independently run 22-process proof passed all four disclosed source states, seven negative ownership variants and 55 paired mode comparisons with zero audited runtime file reads, unchanged sources and exact unrelated semantics/payload hashes. See [the reader record](../../../../../re/solidworks/records/SdkNamedBodyRead2026.md) and [the native owner investigation](../../../../../re/solidworks/records/NamedBodyOwnership2026.md). Native writing and original held-out acceptance remain separate requirements. [Process receipt](../../../../../re/solidworks/measurements/2026/SdkNamedBodyRead01.json)
