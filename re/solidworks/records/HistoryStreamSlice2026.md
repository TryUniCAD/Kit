# Ordinary SOLIDWORKS 2026 History and Biography streams

The `B04-SW2026-HISTORY-STREAMS` tranche depends on the shared
archive primitives and the Branch write action in PR #199 at
`6a7a542393913c09b923e4032b3329c41ec8562c`. It extracts the
standalone version-19000 scopes measured on SOLIDWORKS 2026
SP05.2 `34.5.2.0604`.
[Build, source and process manifest](../measurements/2026/HistoryStreamSources01.json)

## Measured field boundaries

The exact model image locates the Biography serializer at
`0x4c71ec40`, its embedded record at `0x4c71ea50` and each
start/end record at `0x4c71f700`. Version-history and date-code
history serialize at `0x4c71fb70` and `0x4c71f5b0` respectively.
Both history loaders use their final state. A signed count and the
ordered embedded fields determine each byte position. The version
state's stored version selects its boundary before reading the
date-code link. Embed reuses the existing stamp field rules.
[Pinned loader findings](https://github.com/TryUniCAD/Kit/blob/df25ff93a08d05ddba0f64e2dd7e5eba82e8bdd2/re/solidworks/records/HistoryConstruction2026.md)

The codec keeps the standalone base-one map for each stream. The
Biography root's class and object use slots 1 and 2. Populated
telemetry stays embedded, including each of the start and end
records and their six location tuples. The History root also uses
slots 1 and 2, with the date-code class and object in slots 3 and
4 on the measured controls.

| Disclosed input | Provenance | Biography bytes / records | History bytes / version states / date states |
| --- | --- | --- | --- |
| L1 | SOLIDWORKS-authored ladder, published privacy normalization | 1541 / 2 | 101 / 1 / 1 |
| D19Annulus | SOLIDWORKS-authored analytic discovery, published privacy normalization | 1561 / 2 | 101 / 1 / 1 |
| ConcaveOwned | Kit-generated part with recorded native lifecycle | 23 / 0 | 187 / 1 / 1 |

L1 and D19Annulus have different Biography digests and identical
History bytes. The actual ConcaveOwned History differs. Both
streams retain their exact typed map and re-emit unchanged for
each source. Only the reviewed D19Annulus research CAD fixture
was copied from the pinned aggregate. The queue reads its
checksum-bound release copy.
[D19 corpus custody](https://github.com/TryUniCAD/Kit/blob/df25ff93a08d05ddba0f64e2dd7e5eba82e8bdd2/re/solidworks/v2026/corpus/curves-discovery/PrivacyLedger.json)
· [Earlier saved biography audit](https://github.com/TryUniCAD/Kit/blob/df25ff93a08d05ddba0f64e2dd7e5eba82e8bdd2/re/solidworks/measurements/2026/SdkSavedBiography01.json)

## Model construction

`MakeBiography` begins with zero stored session rows, as accepted
on previous parts, assemblies and drawings. `MakeFreshHist`
uses the caller's typed `HistoryInput` for the creation event,
comment, build, license and language fields. It computes both
counts and writes an actual date-code object. The aggregate
codec's numeric comparisons use the existing shared branch and
bounded signed count actions here. A typed root and date-code
role check guards newly introduced nodes and mapped aliases.

Two independently authored creation events and Unicode comments
match manually framed wire records. A two-state model writes the
actual count 2 over its authored count hint 9. Both states bind
the same date-code object at slot 4, and the caller's count hint
stays intact. The process also checks twelve refusals, including
negative and empty counts, the inner and outer versions, a
truncated telemetry row, a foreign date-role or alias, trailing
data and a malformed authored owner.
[Part construction and native lifecycle evidence](https://github.com/TryUniCAD/Kit/blob/df25ff93a08d05ddba0f64e2dd7e5eba82e8bdd2/re/solidworks/measurements/2026/SdkDefaultPartNative01.json)

```sh
python -I -B re/tooling/sw2026/CheckHistory.py ladder
python -I -B re/tooling/sw2026/CheckHistory.py annulus
python -I -B re/tooling/sw2026/CheckHistory.py concave
python -I -B re/tooling/sw2026/CheckHistory.py authored
```

All four host processes reported zero external accesses after
input loading. The manifest records their digests. The production
codec uses the typed fields and shared scalar, string and map
primitives. This change supplies internal stream read and write
coverage, with zero new native trials, held-out cases or public
writer coverage. Earlier version lanes and additional archive
owners have separate exits.
[Disclosed queue cases](../../../tests/Convert/Solidworks/Archive/HistoryTests.py)
· [Authored queue case](../../../tests/Convert/Solidworks/Archive/HistoryWireTest.py)
