# Ordinary assembly configuration exchange owner

Task `B04-SW2026-MATES-CONCENTRIC/config-header-exchange` in PR #121, owner `assembly_frontier`. Base `2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab`. This slice implements the semantic MessagePack cell for `Contents/3DExperienceExchange_ConfigHeader` and checks its association with the actual model exchange data. The separate UnQLite physical writer owns the database layout and the database creation clock. [Configuration headers](ConfigurationManagerHeader2026.md) · [Override storage](ComponentNameOverrideStorage2026.md) · [CAD acceptance](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Configuration header cell

An ordinary active assembly configuration produces one record with the following exact MessagePack dictionary order. These are the observed orders of the string keys in the native ordered multimap. The current SDK lightweight header contributes the actual name and configuration ID.

| Ordered key | Type | Classification and owner |
| --- | --- | --- |
| `_3dExpType` | Integer | Derived in the exchange writer from signed family member ID at runtime `+0x60`. It writes 0 at the ordinary sentinel -2. The static branch produces 1 for -1 and 2 above -1. |
| `class` | UTF-8 string | Format vocabulary `dmConfigHeader_c` from the registered concrete header class. |
| `configHeaderfamilyMemberID` | Signed integer | Runtime `+0x60`. Both the ordinary constructor and measured files use the no-family sentinel -2. |
| `id` | Integer | Current configuration's persistent ID. `dmConfigHeader_c` uses `+0x30`, while `moConfiguration_c` uses `f08`. |
| `name` | UTF-8 string | Runtime `dmConfigHeader_c+0x10`, joined to the actual selected configuration's name object. |
| `repParent` | UTF-8 string | Runtime `+0x68`. The ordinary constructor initializes it to an empty string. |

The source projector requires one active manager configuration and a lightweight entry with selection state 1, matching ID and name, and no parent. The cell reader requires the exact six-key form and ordinary family and representation state. The writer computes the map structure, compact numeric words and UTF-8 string lengths from the typed model. [Semantic cell](../../tooling/sw2026/para/concentric/ConfigHeaderExchangeModel.py)

Each configuration header owns a distinct canonical 36-byte UUID4 key. In the pinned `34.5.2.0604` `sldarchiveu.dll` with SHA-256 `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`, `getDBKey` at `0x319f8880` lazily fills the header's `+0x70` member by calling the original `sldutu!GetSWGUID` import at `0x31a0e720`. The manager has its own lazy slot at `+0x88` via `0x319f88b0`. The native `GetSWGUID` path invokes `UuidCreate` and `UuidToStringA`. Generation receives a newly allocated UUID for its actual record. [Pinned shared GUID behavior](DownstreamIdentityMembership2026.md) · [Native evidence receipt](../measurements/2026/ConfigHeaderExchange01.json)

The observed serializer `0x319f9f60` reads `+0x60` for the family ID, then uses the family comparison at `0x319fa4a3` for `_3dExpType`. The separate type accessor `0x319f8780` reads runtime `+0x64`. The two positions have independent meanings. The native getters at `0x319f8a40`, `0x319f8af0` and `0x319f8b20` independently confirm ID, name and representation-parent ownership.

## Paired model database and override state

`Contents/3DExperienceExchange2` has a literal `TOC` key with class `object-map`. Its `model` map identifies `moAssembly_c` and supplies `configid` and `configname`. These join to the actual active configuration in CMgr and the config header cell. The model DB also owns a separately keyed `moConfigurationMgr_c` row. Its persistent ID joins the binary manager's `f08` value of -1. Its `overriddenReferenceIDs` array gives the actual empty set in this ordinary profile.

The configuration-header key is distinct from every model DB key in all measured files. On D01/D02/D03 native edits, the configuration-header UUID changed while the model manager's UUID stayed stable. A database clock belongs to its physical store. The configuration join uses the persistent configuration ID and name.

The header manager can write a separate entry when its override tree count at `+0x80` is positive or its single physical-product ID at `+0x90` exceeds -1. The native save branch is `0x319f9337`–`0x319f9356`. The manager's own `to_msgpack` selects the nonempty ID tree at `0x319fa6d6`–`0x319fa6e3`. Twelve measured header databases have a single configuration entry. The model-side manager records all have an explicit empty override array.

The native renamed control saved two actual custom occurrence names `AuthoredAxisA-1` and `AuthoredAxisB-2` at IDs 24 and 25, both on child definition `IndependentNameCylinder`. Both exchange stores still report the ordinary empty override set. The earlier fresh-persistence failure for these names survives. The actual manager set has a distinct mode-gated producer. Name divergence cannot determine the persisted ID set. The scope refuses a populated override owner. [Native renamed contrast](ComponentInstanceNameWire2026.md)

The model maps retain ordered repeated keys. Each of the three plane records and the selection-set folder has two `class` entries, and the mate group record contains both `moMateGroup_c` and `moNodeList_c`. The `TOC.model` map also repeats `object`. The join checks each singular field only on the owner that publishes it. [Bounded MessagePack parser](../../tooling/sw2026/para/concentric/ExchangeMessagePack.py)

## Offline evidence

The [proof driver](../../tooling/sw2026/para/concentric/ProveConfigHeaderExchange.py) verifies the six disclosed D01/D02/D03 source and edited parents, five independent assembly controls and the separately pinned renamed parent. All twelve joins match. The six-field map is 92 bytes in each saved file, and its data bytes reproduce exactly by projecting its actual linked configuration and lightweight entry. The reader sees eight model exchange records in every case, including seven UUID keys separate from the header UUID.

Two isolated, stdin-only workers use the normal neutral assembly constructor and its actual current configuration to build fresh cells. They verify the previous complete persistence parent and child and change the second authored configuration's name, including Unicode and a longer string length. Each graph has its own allocated UUID4. Eight malformed or unqualified owner cases refuse. The audit captures zero runtime input accesses. [Measured output](../measurements/2026/ConfigHeaderExchange01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveConfigHeaderExchange.py \
  --disclosures /path/to/Oracle121Takeover \
  --archive-image /path/to/exact/sldarchiveu.dll > /tmp/ConfigHeaderExchange01.json
```

## Generated parent

The [configuration store composer](../../tooling/sw2026/para/concentric/ConfigHeaderExchangeStore.py)
reads the lightweight directory from the generated parent streams and joins
its single entry to the actual active manager. An explicitly supplied
publication wall clock and separately allocated UUID own the store creation
event. The [shared database codec](UnqliteExchangeStore2026.md) derives the
database framing, hashes, links and free space from that event and the
single generated map.

In the twelve disclosed archives, recomputing the database from its actual
configuration and the observed volatile clock and UUID reproduces the entire
stream byte for byte. Two isolated workers take the same neutral assembly
and two independently supplied creation events over stdin. Both workers
produce identical results for each event. The generated parents carry 33
streams, preserve the other 32 and the complete child, and have zero runtime
input accesses. A repeated publication over the same stream refuses. The
two event choices change the whole parent and preserve the configuration
map. Ten original D01 source members still need construction or admission
evidence. The second model exchange database, platform and family or
representation variants, native lifecycle and held-out qualification are open.

[Generated parent receipt](../measurements/2026/D01ConfigHeaderStore01.json) · [Proof driver](../../tooling/sw2026/para/concentric/ProveD01ConfigHeaderStore.py)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01ConfigHeaderStore.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --output /tmp/UnusedD01ConfigHeaderStore.json
```
