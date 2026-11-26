# Observe the saved Boss direction owner

The deterministic semantic comparison report can record a source-bound direction reference for a supported SOLIDWORKS P03 Boss. It uses the actual feature that consumes the sketch and the native sketch named by the saved direction record. The selected `N_Axis` must agree with the supported Front-plane normal.

## Use the observation

Run the existing [semantic graph comparison](../../../../Reference/Research/SemanticComparison.md) with two sealed typed documents. Use the same SDK model revision that emitted the documents. The [independent P03 readback](../../Encoder/ConstrainedBossSdkReadback.md) describes the two separately retained document inputs.

Inspect `sources.left.observations` and `sources.right.observations` for `reader_reported_native_direction_owner`. Each observation identifies the source digest, selection, operation, sketch owner, sketch and support plane. Its native span refers to the direction record's owning feature. The IDs are local to the read document. Compare each side by semantic role.

## Scope

The check requires a unique supported operation, sketch owner and target. The feature links, retained archive identity, principal direction and native provenance must agree. Name-only paths and contradictory or duplicate candidates produce no direction-owner observation.

The report retains the original native selection and all unresolved entries. Its comparison status and qualification fields stay under the existing rules. The direction observation does not establish full source history, B-rep, native edit or save/reopen, or public writer admission.

## Verification

The maintained process test passed in 25.53 seconds on Windows Python 3.14.6. It captured the pinned P03 source and ran the existing comparison five times. Both unchanged inputs produced the observation. Wrong owner, target, normal and provenance controls withheld it. The comparison kept its `different` result and all 188 unresolved classifications. The final maintained process test added an independently authored right archive and passed in 44.04 seconds. A fresh strict design-only SDK read found right Boss 71 to sketch 57 at span 12036 + 3025. The left archive retained Boss 34 to sketch 26 at span 11996 + 3037. The right archive SHA-256 was `1bf203d3dfbaac409eb3960907b86b56de1da980c40622b75678aba1682e2f9a`. The existing wrong-source controls retained their results. Nine existing comparator compatibility cases passed in 6.19 seconds.

A separate run used the exact #121 SDK codec and both strict design-only documents from [PR #328](https://github.com/TryUniCAD/Kit/pull/328). The source sealed feature 34 to sketch 26 at native span 11996 + 3037. The candidate sealed feature 71 to sketch 57 at native span 12036 + 3037. Both use Front plane 2. The report retained all 57 matches, four reference differences and 188 unresolved entries on each side. All previous report fields stayed equal after excluding the two new observations and the implementation hashes. The output SHA-256 is `f0438fa37ec223ba1ddc02c8b40f0f9ba8e4ec76db8f26bd98b138c04d1987f7`.

Twelve additional controls across both exact reader outputs passed typed input validation. Each withheld the direction observation and retained the original unresolved path and reason counts. The wrong-owner controls used an internally consistent selection proof for the wrong feature. The control evidence SHA-256 is `874eff50a055c38c443a9e51d241391867fd78391ef7c6e404af4fb212a1d883`. No vendor application or model calls ran.

The maintained generated archive test forces cp1252 inside its isolated child and uses a non-ASCII path. It passed in 34.89 seconds. A separate fresh child with cp1252 text output settings reproduced the original encoding error. The repaired binary pipe returned the exact UTF-8 path and unchanged archive digest. [Direction readback encoding gotcha](../../../../Gotchas/Research/Readers/ConstrainedBoss/DirectionReadbackEncoding.md)

[Direction selection name gotcha](../../../../Gotchas/Research/Readers/ConstrainedBoss/BossDirectionSelectionName.md) · [Task register](../../../../Reference/Research/AutomationSteps.md#a06-comparison-implementation-and-qualification)
