# Internal plain-part adapter preparation

The new internal `Core/Preparation/PreparePart` boundary accepts a real neutral
rectangle document, ordinary destination and `WriteOptions`, plus the existing
explicit typed construction recipe. It returns a complete SDK-only blind-boss
`PartCandidate` and preserves actual graph aliases. It writes no destination and
asserts no vendor/application acceptance.

Neutral geometry, units, support and configuration identity control the result.
The recipe retains presentation and provenance fields that the neutral document
does not yet model. No new public option, saved source file, template, installed
preference or research runtime is introduced. Unsupported source domains reject.

The bridge uses the existing `final_destination` staging value for native self
identity, requires matching staged/final filenames, and keeps the present absolute
Windows path boundary explicit. Unmapped host paths and unnamed streams reject;
binary preparation with an explicit final identity leaves the sink unchanged.
See the [destination gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Construction/FinalDestinationOwnsNativeSelfIdentity.md).

Public SOLIDWORKS support remains read-only. `SldprtAdapter`, SDK registration,
default open/save behavior and write availability are unchanged. The bridge is
not called by a public adapter and cannot enable writing through an option.

The permanent process case covers two authored neutral inputs, exact full-file
constructor comparisons, ordinary public readback and continued public save
rejection, with twenty-one invalid requests per design. Scoped static checks
passed. The corrected independent 4,595-source snapshot passed the permanent
integration and both separately retained guarded workers: forty-two rejections,
zero runtime input reads/research imports, exact direct-constructor bytes and
successful public readback. The generated containers are 8,168 and 8,256 bytes;
public save still rejects without mutating its destination. The
[process receipt](../../../../re/solidworks/measurements/2026/SdkPlainPartPreparation01.json)
binds the complete raw reports and source closure. The
[format and scope record](../../../../re/solidworks/records/SdkPlainPartAdapterBridge2026.md)
binds the exact source snapshot and separates this preparation boundary from
native, held-out and public writer admission.

The first frozen replay rejected a lazy public-reader code import inside the
strict read guard before any model input read. Its snapshot is preserved. The
causal retry adds explicit code imports before the same guard; no SDK behavior or
read policy is relaxed. See the [code-preload gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Construction/PublicReadNeedsCodePreload.md).
