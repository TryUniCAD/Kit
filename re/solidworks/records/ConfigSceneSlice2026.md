# Ordinary SOLIDWORKS configuration scene records

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-SCENE` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-light-actions` |
| Preparation base | `62dbec1255b151b0cd0be00aa18b84cdfe26a873` |
| Prerequisites | [Bounded feature actions](ConfigFieldActionsSlice2026.md), [thread and mark records](ConfigThreadMarkSlice2026.md) |
| Exit | Guarded typed reads of both disclosed scene profiles, independent wire contrasts and ownership refusals in the merge queue, then current revision review |

## Independent field-order evidence

The SOLIDWORKS 2026 SP05.2 `34.5.2.0604` model image has SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The complete light base serializer at `[0x4bc0b030,0x4bc0b9ec)` has
SHA-256 `c066072b10393f52a94b6dd9f1b97d079906824abcab4439ee0b1bc35afd1cd7`.
Its reader consumes the signed `f36c` word and clears the runtime
member. The typed body retains the word under `f36c#wire`. The two
`f384` occurrences also retain independent positions. A native
runtime reset or duplicate store does not establish a new document
default. [Native span evidence](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/AuthoredAmbientConstruction2026.json)
· [Wire state evidence](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ArchiveWireState2026.md)

The environment-folder virtual serializer at
`[0x4beb1bc0,0x4beb1cb0)` uses the inherited feature fields and
two ordinary signed suffix words. The concrete environment, ambient
and directional classes use the same four virtual targets already
established for this feature base. The directional suffix adds a
three-double vector and one double after the common light record.
The archive's earlier name class owns a CString field used by all
scene owners. Runtime descriptors for the environment, two light
classes and name class give file schema one.
[Environment and virtual owners](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/CommonPartOwners2026.md)
· [Native descriptors](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigRuntimeDescriptors2026.json)

The existing bounded member reader owns the per-class map and body
executor. Only the scene role allows light and name children. Its
inherited feature fields and directional vector use the shared field
layouts. The reader requires distinct newly allocated light and name
objects, an ambient root entry followed by independently validated
directional entries, empty resolved lists in the lights, and empty light
user property owners. Validators register alongside existing bounded
members. The new runtime normalization retains its own zero projection.

## Disclosed physical profiles

The [source manifest](../measurements/2026/ConfigSceneSource01.json)
binds both tracked part hashes, complete Config-0 digests, their
earlier name declarations and every scene, light and name interval.
The full reference reader was observed at
`9812f561bca43a7a303134799a4ab6d5307b6a74`. Its scene read
and container implementations retained the aggregate layout at
`f4fc8744235448c0ff6048e4447440bb7927a6d1`.

| Control | `moPart_c.f1e0` | Scene map counter | Owned objects |
| --- | --- | --- | --- |
| L1 boss | [20734, 22222) | 69 to 82 | Environment 70, ambient 73, directional 76, 78 and 80 |
| ConcaveOwned | [18861, 19392) | 54 to 60 | Environment 55 and ambient 58 |

Both real scenes refer to `moNodeName_c` class slot 4. The guarded
process first decodes the actual earlier part name at object slot 5
and carries those map entries into the scene at its observed counter.
The L1 directional lights all use the same class object in slot 75.
Their feature objects and name objects remain distinct. The ambient
and directional records preserve the observed values and actual
owner boundaries when the earlier map entries remain available.

The independently authored numeric contrast replaces the declared
Concave light words in memory with signed `-739`, `27` and `-16`.
The shared normalization retains `-739` on the wire side, records
zero on the runtime side and preserves both `f384` occurrences.
Two count contrasts change the declared L1 child count and retain the
matching leading native child frames. The reader accepts one and two
directional light cases with counters 69 to 78 and 69 to 80. Both
retain the actual ambient owner and all inherited identities. The
post-change guarded reports have SHA-256
`4f7a8ea1da698be7f0b81af1ba793349f43b550a2424d547b5b3abaf63ae88c9`
for L1 and `0daf87b3454802d6ae5cea92a234234cd65a259ee359f7bc0320431e8b3eeaa3`
for Concave.

The malformed controls cover incomplete and trailing records, wrong
archive version, unsupported root and nested classes, missing class context,
borrowed or repeated objects, absent required lights and populated
property state. The in-memory body reads deny file and external
runtime access.

## Independently saved one and two direction controls

The disclosed independently authored `OneLights.SLDPRT` and
`TwoLights.SLDPRT` were saved and reopened by SOLIDWORKS 2026
`34.5.2.0604`. Both native author/reopen pairs and both bracket
controls passed, with 14 numerical checks per candidate phase.
The canonical eight-process packet is SHA-256
`e716b46e72d8f37081cdf5bf7ca7832d5a3445532bed7a840e631d497b305081`.
Its aggregate outcome remains false because the separate property
getter arm failed. These two disclosed cases carry zero held-out or
production qualification.

[Checksum-bound source and phase manifest](../measurements/2026/ConfigSceneCounts01.json)

The independent full Config trace on aggregate revision
`db7a68ef02fa0ac4cb9d7711d59ee053861d870d` binds the physical part
root, header aliases, earlier separate name, scene, all light and
name scopes, and the six linked stream hashes. The full typed probe
receipt SHA-256 is
`c413d0be30786fafa782749b7e21c0d6f57093b226727fc89abd707917147423`.
The repository copies match the native save hashes. The guard reads
the actual earlier name at slots 4 and 5 and retains those same
entries. Slots outside the bounded role remain unmaterialized. All
scenes are read by `ReadCfgMember` with the original ordered records.
Both new source controls reuse stock light values in parts of their
records. Their native owner scopes, counts and complete source
digests were measured independently.

| Control | `moPart_c.f1e0` | Scene map counter | Child object slots |
| --- | --- | --- | --- |
| OneLights | [20822, 21668) | 70 to 79 | Ambient 74, directional 77 |
| TwoLights | [20822, 21989) | 70 to 81 | Ambient 74, directional 77 and 79 |

Both scene roots are at slot 71. The separate names are at slots 72,
75 and 78, with additional name slot 80 in TwoLights. Both directions
in TwoLights use the same class descriptor at slot 76. The signed
`f500` property counts are zero in every light. The guard separately
checks the physical scene and name hashes, the typed root descriptor
and the native stored row count. Its original L1 and Concave reports
matched byte-for-byte after adding the two cases.

The two new guarded host reports carry zero runtime external access.
The OneLights report SHA-256 is
`afb269ccd4f7e2c894accf9b9b21f6e4af550befc10d93c77bdf5537363c9658`.
The TwoLights report SHA-256 is
`03e724fdd93e3b5d6b257992bb90bc13c6daf0943b1f6bc350129ab3b6526fae`.

```sh
python -I -B re/tooling/sw2026/CheckCfgLights.py ladder
python -I -B re/tooling/sw2026/CheckCfgLights.py concave
python -I -B re/tooling/sw2026/CheckCfgLights.py one
python -I -B re/tooling/sw2026/CheckCfgLights.py two
```

Queue execution of the updated process cases remains pending.
[Original cases](../../../tests/Convert/Solidworks/Configuration/CfgSceneTests.py)
· [OneLights case](../../../tests/Convert/Solidworks/Configuration/OneLightTests.py)
· [TwoLights case](../../../tests/Convert/Solidworks/Configuration/TwoLightTests.py)

Further Normalize modes, populated properties,
other scene classes and user-facing presentation semantics remain open.
Complete Config-0 admission still needs the model and part sections,
direct owner binding, context and ghost bookkeeping, cache readers,
the broader layouts and complete stream exhaustion. This record
qualifies the listed typed read boundaries.
