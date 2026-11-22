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
ordinary resolved grammar stays unchanged. The published aggregate
contains no hosted SOLIDWORKS saved-sweep test. The two-fixture test
and its scrubbed CAD assets remain on #245.

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
