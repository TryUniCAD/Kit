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
objects, empty resolved lists in the lights, and empty light user
property owners. These restrictions preserve the observed presentation
boundary. The only new runtime normalization mode is the zero
projection.

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
The malformed controls cover incomplete and trailing records, wrong
archive version, unsupported root and nested classes, missing class context,
borrowed or repeated objects, absent required lights and populated
property state. The in-memory body reads deny file and external
runtime access.

```sh
python -I -B re/tooling/sw2026/CheckCfgLights.py ladder
python -I -B re/tooling/sw2026/CheckCfgLights.py concave
```

The [new guarded process cases](../../../tests/Convert/Solidworks/Configuration/CfgSceneTests.py)
await queue execution. Both reference profiles were observed on
existing tracked files. Further Normalize modes, populated properties,
other scene classes and user-facing presentation semantics remain open.
Complete Config-0 admission still needs the model and part sections,
direct owner binding, context and ghost bookkeeping, cache readers,
the broader layouts and complete stream exhaustion. This record
qualifies the listed typed read boundaries.
