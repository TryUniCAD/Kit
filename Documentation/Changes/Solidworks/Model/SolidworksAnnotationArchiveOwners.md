# Verified SOLIDWORKS 2026 annotation archive owners

The shared research codec explicitly defines 52 dimension, annotation, label, table, helper, frame, detail, format and annotation-view owners from the actual SOLIDWORKS 2026 SP05.2 serializers. Their wire fields and exact dictionary keys are preserved. Existing sorted module discovery loads the nine `VerifiedAnnotation*.py` modules after the provisional ConfigDetail/ConfigPart definitions.

Each owner begins with an effective-version-19000 admission check on both load and store. Historical and future versions fail before owner fields; the existing omitted/zero-version current alias remains. These are ordinary, non-DB archive layouts. No saved defaults, field rows, templates, raw payloads or production writer are introduced.

The note-helper u64 attachment count now follows the native signed-low32 loop rule. The old whole-u64 predicate could silently treat a positive low32 count as zero when high32 was nonzero. The new rule retains the original u64 and row keys, and preserves the shared repetition safety limit. See the [specific count boundary](../../../Gotchas/Conversion/Solidworks/Model/NoteAttachmentCountUsesSignedLow32.md).

## Evidence and use

The [native finding](../../../../re/solidworks/records/AnnotationArchive2026.md) and [complete field record](../../../../re/solidworks/records/AnnotationArchive2026.json) bind all 52 RTTI owner names and primary `+0x28` dispatches to the original 2026 image hashes, file-version resources, native field order, constructor member types, branch/count rules and function hashes. Ortho/misc labels share a native target; arc-length and title-block serializers are verified tail jumps to shared base serializers. No proprietary listing or vendor software is published.

Use the existing [research serializer](../../../../re/tooling/sw2026/serial/README.md) and `RoundTrip.py --require-proven`. The existing remote curve fixture process runs eight primary stream comparisons for each of 26 prepared discovery/control source files, then 26 resolved stream comparisons using `--link-config`. No new workflow or local test invocation is added. Used provisional or missing dependency schemas still fail the strict check, including optional populated GTol schemas outside this change.

The earlier retained reports had 208/208 primary and 26/26 linked byte identity with zero tails, but only 104/208 and 0/26 strict passes because used owners remained provisional. All 52 changed owners were reached in both earlier reports. Those pre-change counts do not establish compatibility of this revision. This worker performed only AST/format checks, original-image static analysis, hashing and JSON arithmetic; no schema imports, product execution or tests ran locally. Fresh remote process compatibility, all current-head CI and configured review remain pending after integration.

## Limits

Raw wire values remain distinct from native runtime repairs, such as font substitution, chamfer clamping, balloon mode conversion and integer-to-boolean normalization. This change supplies no new generative value classification or CAD acceptance. Held-out source payloads remained sealed. The production adapter remains read-only and the full native-writer goal remains unfinished.

The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) state “The first is success under every criterion on this page” and “The second is the end of the available context.” Schema proof and byte identity alone do not satisfy those criteria.
