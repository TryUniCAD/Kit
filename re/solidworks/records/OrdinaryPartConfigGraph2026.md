# Complete ordinary SOLIDWORKS 2026 part configuration graph

Task B04-SW2026-ORDINARY-CONFIG, owned by the #121 takeover team on
codex/solidworks-ordinary-config-graph. The delivery uses accepted main
f80da8caed2ca7a585c1aa85f22c1e13196761d5. It composes the measured
format-4, version-19000 ordinary part layouts from aggregate
05f87aa68097904dae3871292bc8ff969a6cda22 with the currently accepted
header, maps, body actions and bounded owner definitions.
[Native field and map authority](https://github.com/TryUniCAD/Kit/blob/05f87aa68097904dae3871292bc8ff969a6cda22/re/solidworks/records/ConfigBodyGrammar2026.md)

ReadPartConfig selects the physical Config-0 and its actual named
ModelHeader. ReadConfigMut and WriteConfigMut share the same field
rules and use the accepted section and header alias actions. The part
root is installed before light or resolved fields execute. Cursor
exhaustion covers both sections and the enclosing stream. The registry
contains the 144 distinct schema names and 40 descriptor pairs exercised
by the disclosed graph union. The two published blind-part reach
profiles each use a subset of this registry. Independent CMgr selection
and the public property and writer entry points have separate delivery
scopes.
[Complete part reader](../../../src/convert/adapters/solidworks/Archive/Config/ReadPartConfig.py) ·
[Typed writer](../../../src/convert/adapters/solidworks/Archive/Config/WriteConfigMut.py)

The complete graph reuses accepted unit, atom, cache, sketch block,
thread, view, scene, annotation, and surface-finish grammar. The part
registrations contain the remaining ordinary model, detail, table,
visual and related owners. The existing bounded layout branches retain
their original refusals for other atom kinds, protected annotation
owners, populated light properties and unsupported cache rows. The
full graph supplies the actual enclosing part for the existing unit
component backlink. The directly owned sheet-metal helper receives
its declared part field and preserves the observed empty body list.
Fixed sixteen-byte model and block fields retain caller-supplied
values or modeled defaults supplied by the caller. Their prior
format classifications remain authoritative.
[Surface finish](ConfigSurfaceFinish2026.md) ·
[Unit member backlink](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Configuration/UnitComponentOwnsEnclosingPart.md)

## Guarded observations

Each row is a fresh isolated Python process. The same node identities
occupy every archive map slot after emission, including actual part
slot 2 and original ModelHeader self slot 3. All archive operations
run under a guard with zero file, network or CAD runtime accesses.
The typed result and unchanged original consume the same two windows.

| Case | Config-0 bytes | Lightweight span | Resolved span | Final map counter | Unit owner span |
| --- | ---: | --- | --- | ---: | --- |
| L1 ladder | 25,390 | [18, 3052) | [3056, 25390) | 110 | [2435, 2437) |
| ConcaveOwned | 22,700 | [18, 2105) | [2109, 22700) | 94 | [1722, 1724) |
| RectangularBare | 22,706 | [18, 2111) | [2115, 22706) | 94 | [1728, 1730) |
| CircularProperties | 26,055 | [18, 3058) | [3062, 26055) | 122 | [2441, 2443) |

The one-byte lane, truncated second section and trailing byte refuse.
A same-width unit backlink substitution names the real but incorrect
header object at slot 3. Both that input and a detached typed writer
owner refuse. The complete literal control is read directly from its
existing PR Git object. The branch adds no source CAD fixture.
[Physical evidence](../measurements/2026/OrdinaryPartConfigGraph01.json) ·
[Fresh process probe](../../tooling/sw2026/CheckOrdinaryCfg.py) ·
[Queue cases](../../../tests/Convert/Solidworks/Configuration/Complete/PartConfigTests.py)

Run the probe with Python 3.14, isolated mode and bytecode creation
disabled, once for each case name ladder, concave, bare and literal.
The literal case requires the Git object named in the script. The
queue uses the tracked ladder and concave controls and the separate
authored configuration variant described below.
The scope establishes typed byte replay and enables a later
ordinary native composer. Fresh native, held-out and conversion
acceptance remain separate.

## Retained wire forms

The density unit's nonzero byte owns the subsequent node field. The
complete writer preserves the byte for an explicit null or concrete
node. The typed control uses 167 with a null tag and 99 with a new
length-format node. Dropping that byte used to emit 0 and 1 for these
same inputs. A missing node field with an explicit nonzero byte refuses.
The narrower standalone unit-table admission continues to require its
original absent override.

Signed length fields preserve a word that still describes the actual
repeat rows under the declared count mode. Four modeled empty repeats
retain -7, -13, -19 and -29, including one nested record. The prior
length writer emitted zero for all four. A stale count of -23 with two
modeled rows derives 2. This applies to the native `Positive` pairings
and the block map's `SignedPositive` pairing. The separately bounded
atom-manager writer derives its count as before. Its existing authored
controls still produce counts of 0, 1 and 2.

A fresh typed sheet-metal master belongs to the enclosing part's
`f1018` field. The variant adds it to the hash-pinned ConcaveOwned
configuration graph and changes the measured length and density fields
using authored values. No additional CAD fixture enters the queue.
The author-supplied caption and embedded width survive. The owner
occupies [22663, 22834) and leaves the map counter at 94 across the
field. The whole stream's counter grows to 95 only for the new
length-format object. The populated master and wrong concrete class
refuse. The older member proof continues to refuse the same `f1018`
field when it lacks its real enclosing part.

The core configuration reader binds its root through the focused
`ReadCfgBodyMut` callback. It still validates the root before reading
either section. The four disclosed native streams retain their
original extents, map identities, SHA-256 and byte-exact replay. The
authored archive variant and older boundary probes are host evidence.
They establish no new native acceptance.

```sh
python -I -B re/tooling/sw2026/ProveConfigVariants.py authored
python -I -B re/tooling/sw2026/CheckCfgFieldModes.py authored
python -I -B re/tooling/sw2026/CheckAtomEmission.py ladder
```

[Variant and exact-source receipt](../measurements/2026/OrdinaryPartConfigGraphReview01.json)
· [Queue variant](../../../tests/Convert/Solidworks/Configuration/Complete/ConfigVariantTests.py)
· [Native prefix gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Configuration/EmptyFieldsRetainNativePrefixes.md)
