# Ordinary SOLIDWORKS part cache records

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-CACHES` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-caches` |
| Preparation base | `0cd540e298655e091bcfb4a984ba50e793d67c53` |
| Prerequisites | [Body values and counted rows](BodyValueSlice2026.md), [length and repeat](ConfigMemberFieldsSlice2026.md), [branch dispatch](ConfigFieldActionsSlice2026.md) |
| Exit | Exact bounded fields and preserved archive map in fresh processes, malformed cases through the normal queue, current revision CI and configured review |

## Native field rules

The model module from SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`
has SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The `moPart_c` save span `0x4c237d09–0x4c237d6e` and load span
`0x4c237d79–0x4c237dfc` define the zero-through-two signed cache count
and the signed `f1638` word after the second slot. The direct slot
serializer `0x4bc1dcd0` uses vtable `0x4cf966d8`. It reads a signed
row count and a signed atom ID, signed integer and binary64 value per
row. A populated slot calls the 33-field `moMassProp_c` serializer at
`0x4bc1e185 → 0x4bc1e1b0`, which includes two CStrings and three
embedded vectors. These records allocate no tagged objects or classes.
[Pinned module and call bindings](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/SavedPartMetadata2026.md)

Bounds cache load `0x4b797c20`, store `0x4b797cf0` and cleanup
`0x4b7975f0` distinguish the count from its following key and object
rows. All seven disclosed configurations in the pinned reference trace
have a zero bounds count. The bounded SDK reader consumes only that
count and refuses a populated bounds cache before reading a row.
The property data are derived caches. The selector's semantic
interpretation and canonical bounds key ownership remain open.
[Wire and classification evidence](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ArchiveWireState2026.md)

## Physical controls

The full configuration reader pinned at
`f4fc8744235448c0ff6048e4447440bb7927a6d1` measured these half-open
intervals from the decoded `Contents/Config-0` stream. Each invocation
was in `moPart_c.FUN_4c2378b0` with `f161c=0` and clear archive
conditions. The incoming and outgoing counters agree for each interval.
The complete seven-control census and hashes remain in the
[process receipt](../measurements/2026/ConfigCacheReader01.json).

| Control | Mass `f1628` and physical trailer | Mass map | Bounds `f1640` | Bounds map |
| --- | --- | --- | --- | --- |
| L1 boss | [25151, 25155), zero slots | 108 → 108 | [25370, 25374), empty | 110 → 110 |
| ConcaveOwned | [22654, 22658), zero slots | 94 → 94 | [22680, 22684), empty | 94 → 94 |
| Disclosed CircularProperties | [25542, 25820), one slot with atom 101 and integer 107 | 120 → 120 | [26035, 26039), empty | 122 → 122 |
| Disclosed PropertyPolygonDiscoveryEdited | [25564, 25850), two slots, first empty, second with atom 101 and integer 105, signed trailer 0 | 120 → 120 | [26065, 26069), empty | 122 → 122 |

The host verifier requires exact file, configuration and ModelHeader
hashes before selecting a field interval. It seeds an ordinary part
root from its actual wire descriptor and parses the genuine ModelHeader
alias. The cache records contain no map links. Their bounded checks
retain these three relevant slots and the observed counter, leaving
unused intervening map entries unmaterialized. The caller's part and
map entries retain their identity.

An independent struct decoder checks every cache field alongside the
production field executor. A frame authored separately from the format
rules exercises an empty slot followed by two atom rows, a complete
property body with ANSI and UTF-16 text, and a signed trailer of −17.
The malformed frames exercise invalid counts, a truncated trailer,
surplus data, a populated bounds row, an absent part owner and a wrong
archive version. An audit guard covers the bounded reader after the
fixture and shared header context are loaded. Two runs per case produce
identical reports. The [tracked record cases](../../../tests/Convert/Solidworks/Configuration/CacheNativeTests.py)
and [authored frame case](../../../tests/Convert/Solidworks/Configuration/CacheWireTests.py)
are discoverable by the normal merge-queue test planner.

```sh
python -I -B re/tooling/sw2026/CheckCfgCaches.py ladder
python -I -B re/tooling/sw2026/CheckCfgCaches.py concave
python -I -B re/tooling/sw2026/CheckCfgCaches.py authored
python -I -B re/tooling/sw2026/CheckCfgCaches.py circle --disclosed-root /path/to/disclosed-controls
python -I -B re/tooling/sw2026/CheckCfgCaches.py polygon --disclosed-root /path/to/disclosed-controls
```

## Remaining closure

Public physical configuration admission still depends on the model and
part sections, direct owners, archive context and normalization,
presentation, view and material owners, and complete ModelHeader
binding. The cache tranche is an internal field decoder. It establishes
no cache generation or native application acceptance. Populated bounds
admission requires exact tagged owner and map evidence.
