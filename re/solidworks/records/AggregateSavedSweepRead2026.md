# Saved Standard sweeps in the aggregate reader

PR #121 integrates the bounded saved Standard sweep reader from #245
`84bed4175c2daf7fa50d10757ea83f667d03521f` on published base
`37bedafa1150fdb718012d47cb00d7030adcac6d`. Before integration the
strict generic read returns rounded drivers and a generic native row.
Its linked archive stops at `moSweep_c` schema 1. The aggregate already
has the actual Config-0 and CMgr paths and the ordinary saved references.
The port installs only the remaining sweep-specific resolved schemas
for the explicitly selected saved context.

The reader checks the active configuration, both sketches and their
physical ghosts, actual prior history and face references, the live
result atom, its manager stamp, the partition and rollback marks,
physical density, body name and appearance, and both torus and cap
rim orientations. With geometry requested it decodes the checked
partition and binds both signed rim trims to the same body.
Design-only reads still run the physical and trim checks and retain
topology and editable ownership. They skip neutral B-rep construction.
Raw extraction and unrelated reader scopes retain their existing routes.

The six disclosed source states include two originals, two independent
Section edits and two independent Path edits. The source author lock
and both healthy controls are retained in #245. All six guarded worker
observations agree with #245, including both exact D1 values, the
17-degree Section edits, frame orientation, the body and atom, the
independent native mass properties and altered owner refusals.
The only neutral model difference in twelve comparisons is the
aggregate's explicit `output_body_ids` edge, which links the actual
sweep and its sole saved result body. The port uses no private inputs
or CAD runtime.

The original and Section-edited Wide fixtures already tracked on #245
are sufficient for the standalone branch contrasts. The aggregate
worker enters partition framing, torus and trim validation once in
both read modes. It enters neutral B-rep decoding once in the full read
and zero times in design-only. Six malformed optional XML variants
refuse in strict mode. Permissive reads preserve 27 feature rows and
one body, with zero package layout opens on this aggregate. The
ordinary resolved grammar stays unchanged. The aggregate's shared
complete-suite case repeats strict full and design-only reads with both
scrubbed fixtures, checks their exact driver values and result
ownership, and verifies that neither read is eligible for cold writing.
[Hosted case](../../../tests/Convert/Solidworks/SweepReading/SavedSweepTests.py)
[Fixture provenance](../v2026/corpus/saved-sweep/SavedSweepWide01/README.md)

Both prior disclosed generated cold archives are byte-identical across
the aggregate's unchanged preparation, registry, adapter and direct
writer routes. All 22 logical streams reproduce. The existing cold
worker's historical neutral digest check fails on both the pristine
published base and this port because the current interchange adds
the output-link field. The separate cold comparison uses the same
authored and reloaded neutral model, native authority and complete
archive and stream pins. It compares both SDK revisions and the
earlier native-tested hashes. Ordinary saved ladder, imported body,
literal properties and raw sweep read contrasts also retain their
previous outcomes. Saved-to-native publication stays outside this
scope.

[Exact source and control receipt](../measurements/2026/AggregateSavedSweepRead01.json)
[Prior scoped reader and role provenance](https://github.com/TryUniCAD/Kit/blob/84bed4175c2daf7fa50d10757ea83f667d03521f/re/solidworks/records/ScopedSavedSweepSdk2026.md)
[Prior complete suite test](https://github.com/TryUniCAD/Kit/blob/84bed4175c2daf7fa50d10757ea83f667d03521f/tests/Convert/Solidworks/SweepReading/SavedSweepTests.py)

## Exact saved resolved re-emission

Task `B04-SW2026-SWEEP/saved-resolved-replay`, owner `/root/format_proofs`,
delivery #121, base `197a3283267e95167ac716efbe57d3449bab1b15`.
`WriteResolMut(..., ReplaySavedSweep=True)` takes the model and linked
map from the explicit saved `ReadNativeLink` branch. The shared saved
layouts require version 19000, an ordinary compressed part,
`cmgr_f658=1`, the two solved sweep flags and the exact empty inline
configuration body map.

The saved Section graph retains its ten ordered typed cells and their
actual connectivity. The standalone root's next body points to absent
slot 2. The observed transmit order is `1,3,4,5,6,7,9,10,11,8`.
The writer verifies the actual sheet, circle and resident links, then
computes the typed node records, transmit header, compressed frame and
section length. Both wrapped payloads reproduce inside the complete
resolved stream. Each resolved graph has two declared one-element
binary64 display caches. The shared packed scalar writer decodes and
encodes these fields individually. The usage report records zero raw
byte-field operations.

| Disclosed fixture | Resolved bytes | Resolved SHA-256 | Inherited to final map |
| --- | ---: | --- | --- |
| SweepArcWide | 14,601 | `5a98f672aa95cf0b39f9fb3be02603c1071b15f7aa9b8c5a3c1413f4160e9c02` | 110 to 278 |
| SweepArcWideSectionEdit | 14,730 | `e634947e5e06ded00b5706f01327cfde953cf4d482f09a8500148a1ee3b73d8d` | 110 to 278 |

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/ProveSavedSwReplay.py
```

Five fresh guarded workers verify the two saved streams, both pinned
cold controls, and the ordinary L1 resolved stream with zero runtime
reads. Saved inputs refuse the ordinary and cold modes, mixed modes,
alternate body maps, opaque section input and foreign resident links.
The fixtures' scrubbed omissions include Definition and DisplayLists.
This proof covers an existing resolved stream and its recomputed map
under classic zlib 1.2.12. Public saved-to-native export, whole-archive
construction and held-out native acceptance remain separate work.
The ordinary corpus pipeline does not yet select the dedicated saved
sweep schema writer. The guarded receipt SHA-256 is
`8222c9c5767479af779b000ae8f3ecd44dcbd766de2a20a214f9fe72be7eb777`.
[Guarded evidence](../measurements/2026/SavedSweepResolvedReplay01.json) · [Sparse sheet gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/SavedSweepSheetHasSparseOrder.md)
