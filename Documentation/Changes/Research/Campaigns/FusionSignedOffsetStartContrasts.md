# Signed offset starts with independent two-sided extents

## Behavior and scope

Task `A08h-FusionOffsetStart20261127` adds a bounded research package for untapered circular NewBody extrusions with unequal two-sided distances and signed OffsetStart placement.
The [package](../../../../re/Fusion/OffsetStart20261127/README.md) records both distances, offset sign and zero, radius, placement, XY/XZ frame, swapped-side counterexamples and two same-generator parameter holdouts.
Shared decoders, catalogue builders, native workers and production support remain unchanged.

## Replay and evidence

The source commit is `1647204042fca11349eb62a4e495387204648c8b`; the pinned reader is fresh main `91a73de348894a5791a51b977cd6fe0fe677a617`.
Fusion `2706.1.17` generated 57 archives and 79 API observations with healthy controls.
All 1,140 native-field comparisons and 114 production BRep initial table reads pass.
Independent fresh-process verification exercises first distance, second distance and signed offset through edit, restoration, rebuild, save and reopen.
The sealed summary records completed lifecycle counts, process IDs and executable hashes.
The existing controller/supervisor overlaps deterministic offline replay with serial native work, with models disabled.
Use the package's manifest and pinned research CLI procedure to replay committed files into an unused output directory.

## Limits and failures

Strict reads reject all 57 explicit OffsetStart states; explicit partial reads retain 57 documents and receipts with no reader errors.
An initial two-job manifest prefix error remains retained; corrected jobs use the required 16-byte prefix without changing source bytes.
Zero offset retains its native start-definition type; the [gotcha](../../../Gotchas/Research/Campaigns/ZeroOffsetRetainsStartDefinition.md) explains the policy refusal.
Research ASM4 body-identity reconstruction, independent sketch-driving edits, generator independence, broader operations and editable target conversion remain unqualified.
These measurements establish source-native evidence, not complete decoding or conversion acceptance.

The user explicitly expanded this campaign to 27 modelling cases and 139 native saves.
The expansion source `c3a229ecfb1195447b9a532cc66dc975f77418b6` adds 82 archives and 114 API observations, including fractional/extreme distances, large signed offsets, a sign-crossing edit, a YZ frame and four more sealed holdouts.
All 2,780 native comparisons and 278 production BRep initial tables pass across both groups.
Strict reading rejects all 139 at the existing offset-start guard; partial replay preserves 139 documents and receipts with zero reader errors.
The initial eleven fresh processes passed all 165 lifecycle/control/process comparisons; sixteen expanded fresh-process jobs are running under the same serial resource.
The initial and expanded source commits and reader checkout remain independently pinned; models remain disabled.
