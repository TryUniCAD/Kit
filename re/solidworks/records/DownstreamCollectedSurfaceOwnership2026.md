# Shared collected surfaces in SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns this projection and its native qualification. The selected branch uses one ordinary rectangular blind boss with one applicable cap or side ID per face and no permanent edge representations.

## Representation ownership

The cache builder publishes the temporary collector at `0x4db5dd18` before it builds the face and edge rows. At the end it moves the collector's `+0x1b0` vector to the cache's `f40`. Each native vector item is the separate collected clone of its primary surface, with its own keeper and file object. The string handles for the common file and path are shared across those file objects. [Collector population](DownstreamIdentityMembership2026.md) · [Clone ownership](DownstreamCollectedSurfaceClones2026.md)

| Consumer | Selected branch |
| --- | --- |
| Face own and adjacent surfaces | The loop at `0x4bc141f0` calls `moFace::getSurfaceId`. That method checks the active collector at `0x4be9b206` and dispatches to `0x4b518fb0`. The actual face key finds its singleton candidate. Kinds 40 and 74 carry the required feature and creation words. The native selector returns the candidate index, so `0x4b519065..0x4b51907b` fetches the existing vector entry. |
| Edge left and right surfaces | The batch pair dispatcher calls `0x4b517f90` when its special-kind predicate finds no kind 122. With one candidate per face from the same feature, both candidates share the feature word at key index one. The pair lookup keeps that pair and retains the existing vector entries at `0x4b51835d` and `0x4b518377`. |
| Edge start and end surfaces | Both boundary edge lookups reject the absent permanent representations. Their two fallback faces follow the single-face collector lookup. |
| Inline wrapper | `0x4c6cee50` retains the incoming representation and stores that exact pointer at wrapper `+8`. Ordinary mode-0 model externalization retains the pointer when the feature's filed owner is the supplied model. The two cap/side virtuals share that decision. [Local model-context path](DownstreamStoredFaceState2026.md) |

The six collected representations therefore back all 30 nonnull face slots per prism. Each face still has its own null separator. Object references in the cache archive must reuse the existing mapped representation identities. The earlier direct constructor projection exercised a separate object graph before the batch path was bound. Its archived receipt remains useful for that direct path.

## Verification

The [numeric source ledger](DownstreamCollectedSurfaceOwnership2026.json) and [source receipt](../measurements/2026/DownstreamCollectedSurfaceOwnershipSource01.json) bind 15 complete functions and four instruction windows to original `sldmodu.dll` in SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. REA independently binds the original AMD64 PE artifact digest. The replay uses the existing [source verifier](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) with its `--bin-directory`, `--record` and fresh `--output` arguments.

Two fresh processes per prism verify all 60 model-derived face slots and 12 distinct collected surfaces across the two designs. The six collected objects per cache are shared by reference identity after binary readback. The selected cache map counter decreases from the earlier direct-plus-collector witness's 108 to 47. The face lookup table variant uses 54. Both variants keep all eleven generated input streams. The direct constructor versions still reproduce their previous values. [Combined process receipt](../measurements/2026/DownstreamPrismReferenceReplay01.json)

The supported graph covers this scoped ordinary part projection. Alternate collector candidate selections, native linked drawing acceptance and complete writer qualification remain open.
