# Ordinary planar registry saved readback recovery

The disclosed default-registry lifecycle passed all four native stages and the independent saved readback passed. The original aggregate remains failed. It mixed the public SDK read with a process that had already loaded the COM observer, so the public reader's existing CAD dependency check rejected it. [Original method](SdkPlanarRegistryQualification2026.md) · [Readback recovery receipt](../measurements/2026/SdkPlanarRegistryReadbackRecovery01.json)

## Immutable native evidence

| Item | SHA-256 |
| --- | --- |
| First failed summary | 8efd93beb3f017240bd6eb1ab27678fcef1f21252023fc38180853dfd62951a4 |
| First evaluator | 2685b650ff596fd6ba689f658f508d3748b436251c31f2ba6535c8e88a00db8f |
| Fixture | 33d6f617549610329ef93badc5ec163264de7a5a5440d9f4bb29c09a09ff5160 |
| Saved parent | ab1164708763381c3498ad8bc7b6841a09823f94bf52038685f67ad61902af56 |
| Saved child | 670d8a2fb9c9c03a643dceceb5ac35ce9c1c6095ba7384a08b48b0b710dc1702 |

The preserved reopen phase contains a passing native record, both passing analytic states and the postflight error `ValueError('public native read imported a CAD runtime dependency')`. The first summary combines that postflight with its tree signature condition, so its overall `trees_and_owners_retained` field is false. The recovery compares raw tree and owner signatures independently of that aggregate. It checks the exact Phase and Record hashes, entered file hashes and open modes, ordered process lifetimes, owner observations, all numeric check statuses, role-specific rebuild and edit calls, and the child-first save order. The four underlying exact SOLIDWORKS 2026 SP05.2 processes passed with 80, 120, 80 and 80 numeric checks, zero native errors or warnings, and two healthy A22 controls. [Original phase observer](../../tooling/sw2026/InspectCombinedPlanarMates.py) · [Host recovery verifier](../../tooling/sw2026/planar_registry/RecoverPlanarRegistryReadback.py)

The generated parent and child retained their complete 26/25 ordered native trees through edit and reopen. Occurrence, datum, mate and configuration owners matched. The actual dimension survived the edit from 42 to 57.73 mm. Native parent volume was 12,835.116 mm³ and area was 4,832.28 mm². The parent centre of mass moved by 7.865 mm along Z, from 25.65 to 33.515 mm. The native save returned zero errors and warnings for both files. The fresh open observed the saved child stamp 144 and its native rebuild reported 158 in memory. The subsequent readback verified both saved file hashes again. The four per-role raw and wrapper hashes and actual mass observations appear in the new receipt. [Native acceptance criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#c5-to-c7-loadable-usable-and-measured)

## Independent SDK readback result

The recovery runs the existing frozen public read entry in a fresh Python subprocess with `-I -B`. The worker PID matches the actual spawned process and the existing CAD dependency check returns an empty import list. The host read recovered the exact saved child, both configurations, two actual occurrences, two mates, four ordered endpoints and all three child drivers. The parent and child re-emitted 7 and 6 scoped linked streams byte for byte in memory. Complete saved archive hashes remained exact.

Both actual label positions, owners, witness endpoints and other scoped display values met the frozen comparison. Exact comparison reports two saved away-axis changes. D1's X component and D2's Y component each changed from `0.0` to `6.123233995736766e-17`. The receipt retains those values verbatim, alongside both full display rows. Each falls within the previously frozen absolute \(10^{-12}\) tolerance. [Typed display comparison](../../tooling/sw2026/planar_registry/RectanglePresentation.py) · [Fresh public reader](../../tooling/sw2026/ReadSdkOrderedNative.py)

## Reproduce the readback

Set `PLANAR_PACKET` to the exact disclosed packet and select a new receipt outside it. The verifier checks the frozen fixture, A22 binding, recipe, first observer, all saved inputs and native evidence. It writes a separate JSON measurement. It performs no CAD launch or writer operation. [Recovery CLI](../../tooling/sw2026/planar_registry/RecoverPlanarRegistryReadback.py)

```sh
PLANAR_RECOVERY="$(mktemp -d)/Result.json"
python3.14 -I -B re/tooling/sw2026/planar_registry/RecoverPlanarRegistryReadback.py \
  --packet "$PLANAR_PACKET" --output "$PLANAR_RECOVERY"
```

The host recovery receipt hash is `e1bfbdd16ae433dddd7e454daed897cd3418b5af25e3f578c78bd6df37f6cf3c`. This is readback evidence for the disclosed default-registry fixture. Prior original inputs read, new held-out credits and generated FCStd corpus credits are zero. The exact guest SDK rerun and A20/A21 prior-cohort regression remain separate.
