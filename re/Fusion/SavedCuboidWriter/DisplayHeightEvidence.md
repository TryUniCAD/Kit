# Saved cuboid display associations

## Evidence

[DisplayHeightEvidence.py](DisplayHeightEvidence.py) reads pinned Fusion archives on the saved-cuboid writer branch. Pass each archive as a separate `--case` and supply an unused `--report` path. It reads the typed graph, follows the solid display group to the extrusion's actual body, and validates every leaf bound against the solved cuboid. It compares geometry roles with their order in the original history stream and in the canonical typed re-emission. The experiment leaves source files untouched and invokes no vendor application.

The report `FusionSavedCuboidDisplayEvidence01.json` covers four prior Fusion 2706.1.17 edit and restore pairs. Its SHA-256 is `15bb7013bea0b1ee50bc77e0cf30fb4a3135b84500a5724200fccec52ea597ba`. Its source digests are recorded in the report.

| Observation | Result |
| --- | --- |
| Solid display group and all its leaf references resolve to the active body | 8 of 8 |
| Zero-LOD edge and face bounds match current solved geometry | 8 of 8 |
| Aggregate model box equals current solved geometry | 0 of 8 |
| Display faces follow the typed history face chain | 8 of 8 |
| Display edges and faces each follow ascending physical order in the vendor history | 8 of 8 |
| Unchanged display edges and faces follow ascending physical order after canonical history emission | 0 of 8 |
| Complete typed model equals the model re-read after canonical history emission | 8 of 8 |

The scope contains a single solid, four line sketch and canonical positive XY extrusion. The zero-LOD nodes have no per-leaf mesh payload in this cohort. Face and edge nodes carry distinct qualifiers and a body reference. The start qualifier moved from 72 to 108 between the edited and restored saves in each available pair. Every pair was captured with the same scripted lifecycle, so this does not establish a general qualifier allocator.

The canonical history serializer rearranges physical edge and face slots. The typed model preserves the same topology and graphics through that re-emission. This does not resolve how Fusion joins individual display objects to topology or whether the renderer uses the physical ordering. A native check with a distinct face appearance and fixed-view captures can distinguish a correct display and an accidental role swap.

## One-member native contrasts

[PrepareDisplayContrast.py](PrepareDisplayContrast.py) prepares research-only variants from one hash-pinned vendor save. Pass `--source`, `--source-sha256` and an unused `--output` directory. It preserves the same-source parts outside the selected history, snapshot or material member. The unmodified payload repack controls for ordinary ZIP rewriting. The combined member and complete normalized archive variants distinguish member changes from outer container normalization.

All seven variants for each of the baseline and historical holdout sources retained complete typed-model equality. Each individual change variant differed from its source in only the named uncompressed member. A second fresh process reproduced every baseline digest. The reports carry all archive digests and changed member names.

| Preparation | Report SHA-256 |
| --- | --- |
| Baseline restored source `b6726c11…` | `502f74e0c167b28196af19622a6d2369acf3976c6d5473f62ab3a46173d95f6c` |
| Historical holdout restored source `5e4552d0…` | `b40aa01403049fa47c635d05bbe58e123c84c2edbb23fa2b659d74768857231b` |

These archives are controlled research contrasts. They use the source's own data deliberately and establish no independent writer or native result. Compare the source and repacked control first. Open each one-member variant in isolation and measure edge and face association, picking and appearance before rebuild, when viewport state still comes from the archive. Repeat after rebuild, edit, save and fresh reopen.

## Preview dependency

All 12 previously measured source controls, edits and restores have named 1024-pixel and 256-pixel square PNGs. Both preview payload hashes change between every edited and restored pair. They also differ between each same-height independently authored control and restored archive. Shape, camera and rendering treatment can each contribute. The image headers and hashes cannot isolate these factors.

The constructor's current preview writer emits uniform 256-pixel and 64-pixel images. The saved-profile height writer needs a measured regeneration rule for preview semantics or an explicitly qualified format-supported behavior for derived imagery. Neither copying the old pixels after a height change nor substituting the constructor images is accepted as evidence. Fixed camera, repeat exports, and independent visibility and appearance controls remain necessary.

## Writer acceptance boundary

Run source-unavailable persisted-JSON generation in a fresh process. Require deterministic bytes for fixed writer settings, strict reopening, and complete authored and typed semantic comparisons against independent control expectations. Reject any unsupported leaf, style source, cache state, or extra native metadata transactionally. Then measure those exact generated bytes against healthy independent native controls, including per-face presentation, rebuild and another native driving edit with save and reopen.
