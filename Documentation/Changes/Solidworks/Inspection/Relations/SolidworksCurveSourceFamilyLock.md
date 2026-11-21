# Lock the complete SOLIDWORKS 2026 curve-source family

The [curve-source harness](../../../../../re/tooling/sw2026/AuthorCurves.py) completed all 30 source cases before curve-writer implementation.
The [metadata record](../../../../../re/solidworks/measurements/2026/CurveSourceLock02.json) preserves the source outcomes and verification evidence.
The [portable lock](../../../../../re/solidworks/v2026/heldout/CurveSourceLock.json) binds 24 discovery cases, six held-out sources and two independent controls.

## Behavior and use

The lock records each native source hash, manifest hash, source-tool revision and measured SOLIDWORKS build.
Its case paths use forward slashes instead of Windows separators.
Publication provenance retains the original Windows paths and original raw lock hash.
Native source files remain outside the checkout.

Use discovery inputs for subsequent loader analysis and serializer work.
Keep all six held-out native payloads sealed during rule derivation and writer implementation.
Only independent oracle measurements of future Kit output can establish writer generalization.

## Verification

The complete run used source revision `4ed467bc94a9e7da00bc9782a603a525250242cd` and SOLIDWORKS `34.5.2.0604`.
All 66 fresh phases passed, with 797 passing numeric checks and 100 completed snapshots.
Both rectangle and circle controls passed before and after the source cases.
All snapshots retained the same clean, 25-node feature tree.
The body counts matched their inputs: 91 one-body snapshots, three two-body snapshots and six eight-body snapshots.
The maximum relative volume error was `2.43780292048666e-14`.
The maximum absolute center-of-mass error was `5.863365348801608e-16 m`.

The oracle owner independently checked all 32 native-file hashes.
Publication independently checked all 32 JSON-manifest hashes and the frozen source-tool hashes.
All 797 original checks and all 66 phase outcomes are retained.
Compact proofs cover all 100 snapshots, with complete annulus and capsule discovery witnesses.
Host supervision confirmed parent and transport exit `0` after `2507.983747417 s`.

## Limits

This lock establishes source-corpus acceptance, not acceptance of Kit-written curve files.
Driving-dimension edits rebuilt and were measured, then closed without saving.
The record does not establish edited-file saving and fresh reopening.
The six held-out native payloads were neither parsed nor copied for publication.
The curve writer remains unimplemented, and the production adapter remains read-only.
Local verification used JSON arithmetic, hashes and formatting only.
No local tests, product execution or oracle calls occurred during publication.
