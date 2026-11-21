# Ordinary downstream local owners in SOLIDWORKS 2026

This source-only checkpoint closes the ordinary standalone self-component wire and the local boss surface keeper's file/configuration owner. It does not qualify a generated downstream cache or repair the previously measured warning 32.

Task `B04-SW2026-DOWNSTREAM-LOCAL-OWNERS`, owner `configuration_header`, delivery PR #121. The exit is a reproducible original-source check with explicit runtime-versus-wire ownership and bounded construction inputs. Root owns integration, SDK execution and the vendor oracle. This slice read no CAD document, held-out input or VM state.

## Exact evidence

The [numeric record](DownstreamLocalOwnerContext2026.json) and [verification receipt](../measurements/2026/DownstreamLocalOwnerSource01.json) bind 67 complete function entries, 99 source intervals, 11 concrete virtual slots and 22 imports from eight exact original modules. Function bounds use native unwind ownership and complete small leaves. Private original disassembly is excluded from this packet.

| Original module | SHA256 |
| --- | --- |
| `doccplu.dll` | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |
| `sldarchiveu.dll` | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` |
| `sldgciParau.dll` | `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

The existing [standalone map proof](DownstreamStandaloneMaps2026.md), [component wire proof](DownstreamComponentWire2026.md) and [boundary-role proof](DownstreamBoundaryRoles2026.md) remain separate and unchanged. The present trace adds actual model construction, clone ownership, asymmetric helper contexts and the local external-object path. It does not replace the generic codec with a saved-state program.

## Runtime self component and actual clone

The actual self-component getter at `0x4c0254c0` loads **model + `0x990`**. The earlier `+0xf990` spelling is refuted. The common named-model constructor at `0x4c00d8f0` allocates 40 bytes, calls `0x4b8281a0` with the actual model and stores the result at `0x4c00e85a` in `+0x990`.

The installed primary table is `0x4ce9c4d0`. Its runtime descriptor is `0x4daf1c98`, class `moUnitComponent_c`, native size 40, registered schema `0x80000001`, file schema 1. Its model is held at runtime `+0x20` through a separate 16-byte `moModelHandle_c` created by `0x4be69c90`.

The actual component virtual `+0x158` resolves to `0x4b82ab30`. It allocates a **distinct component** and calls copy constructor `0x4b8280c0`, which asks the source's virtual `+0xa8` for its actual model and allocates a **distinct handle to that same model**. The `moCompRef_c` constructor calls the supplied component's clone at `0x4b7e8313` and retains it in `f58` at `0x4b7e8319`.

Thus separate ordinary edge/face references can hold distinct unit-component objects backed by the same actual model. Reusing a single component pointer everywhere is not this constructor rule. Conversely, the cloned model handle is runtime ownership; it is not a request to serialize the whole model.

## Standalone store and read use different helper owners

The current ordinary paths are deliberately asymmetric:

| Context | Helper constructor | Conditions `+0x10` | Filed owner `+0x30` | Internal owner `+0x3c8` |
| --- | --- | --- | --- | --- |
| `SolidStorage::SaveDownstreamIdDataForPart`, `0x18002fa60` | UI helper `0x496f5680` | 0 | Null | Null |
| Current-model downstream load `0x4b5860e0` | Core helper `0x3c7a8970` | 0 | Actual model supplied by the loader | Null |
| Explicit-config load `0x4b5863c0` | Core helper | Ordinary same model context | Actual supplied model | Null |

The store UI helper retains its `SldModelContext` separately at `+0x38`; that pointer does not populate the filed-owner slot. The downstream setter at `0x3c77bfd0` changes only helper `+0x8bc`. It does not change `+0x10` or install an owner at `+0x30`.

Both helper constructors register the archive address to their helper through `su_CMapPtrToPtr`: UI uses `operator[]` at `0x496f5d2c`, core uses `SetAt` at `0x3c7a8db4`. These are **helper lookup registries**, not `CArchive.MapObject(model)`. The prior standalone-map proof still owns the fresh object-map namespace. No root map tag is invented from a process pointer.

### Selected unit wire and load rebind

For effective version 19000, ordinary local self-unit behavior, helper conditions 0 and the ordinary non-DB archive, the unit body has this order:

| Step | Actual serializer owner | Wire |
| --- | --- | --- |
| 1 | `su_CObject::Serialize` | No bytes with DB-specific flag `0x10` clear |
| 2 | `moComponent_c::Serialize`, `0x4c21cac0` | One raw null `CObject` tag |
| 3 | `moUnitComponent_c::Serialize`, `0x4c22c190` | `u8(0)` for `has_ext` |

This is three body bytes with the generic two-byte null tag, excluding class/object framing and enclosing reference fields. The runtime model handle is absent from this body. The pre-`0x3b3` old-model object is a separate, unqualified version branch.

The base store path checks mask `0x82006000` at `0x4c21cbe8`. With conditions 0, `0x4c21cc1a` selects helper `+0x30`, which the actual store helper initialized null. The raw object writer is at `0x4c21cc01`. The unit writes its zero suffix at `0x4c22c4d0`.

On load, the null base owner enters `0x4c21d158`; at `0x4c21d17c..0x4c21d190` the actual helper model is supplied to `setFiledOwner`. The unit's modern zero-suffix branch subsequently calls virtual `+0x320` at `0x4c22c7d0`, supplying that actual model to `0x4b836760`, which creates or updates the runtime model handle.

The selected wire therefore contains no whole part graph and no serialized `moModelHandle_c`. A typed writer should project the standalone null owner and retain the real model context separately. A generic `owner = root` object field would enter a different body/map graph. Condition 1, owner masks, DB mode, external units and historical versions retain their own branches and are not qualified by this rule.

## Owned local surface references need an actual file/config owner

The ordinary boss's table is `0x4cf3d488`. Virtual `+0x1280` is `moFeature::getOwner` at `0x4bb45da0`; virtual `+0x498` is `getFiledOwner` at `0x4bb44300`.

Surface constructor `0x4c6c2870` constructs a keeper through `0x4bb5d2a0` from the actual feature. A nonnull owning feature creates a persistent `moFR_c` using `0x4bb34670`. The FR's embedded feature identity comes from the actual feature ID, creation time and fresh flag `0x10`.

The FR owner helper at `0x4bb35b20` obtains the actual context's FR manager and calls `0x4bb36e30`. That manager shares the configuration-manager external list when available, otherwise creates one, and obtains a real external file/config object for the actual filed owner. Its returned pointer is stored at `moFR_c.f08`.

No inspected equality shortcut says that a same-file local feature has a null FR owner. A temporary unowned feature and an overload that accepts a null external pointer are different source branches. They do not prove an equivalent null substitute for an owned ordinary boss.

`moFR_c::Serialize` tests `moExtObject::isAlive` and writes the actual typed external object when live. `isAlive` at `0x31a01170` checks membership in the actual live-object set. The named constructor registers its pointer at `0x319fb406`; zero connection counters do not make it nonlive or null.

## Fresh external object: index and configuration are separate

The manager calls `createExtObject(actual filed owner, connection 0, null optional context)` at `0x4bb36eb1`, then shares it through `0x4be96a80` with configuration matching enabled. Existing matching entries can be returned; fresh defaults must not overwrite those entries.

For a genuinely new ordinary zero-connection object, the named constructor at `0x319fb380` supplies zero `f48/f4c/f50/f54/f58/f60/f70` and sets `f78=-1`. The shared file identity is computed from the actual filed owner's path, title/category and **creation** epoch. It is not a captured header or saved self-file record. `connect(0)` is a no-op. The local branch does not substitute the header self-file role's connection count or save epoch.

### `f78` is `IndexInRefList`

Exact exported getter `0x319f8a70` and setter `0x319f9b90` bind the meaning. The list constructor `0x319fb090` initializes its maximum index at `+0x4c` to `-1`. After `AddTail`, share calls `moExtObjectList_c::setExtObjToIndex` at `0x4be96deb`, reaching `0x31a01690`:

- An object whose index is `-1` receives the incremented list maximum
- An already indexed object retains its index; the list maximum rises if that index is greater
- Consequently the first new entry in a fresh list receives index 0

This is not a configuration ID, and it is not unconditionally the current positional list index. Existing indices can survive reuse. Version 19000 serializes the index and then embedded `refcfg`; condition-1 loading can reset the index to `-1`, which is a separate context.

### Active configuration and partition rollback

The embedded referenced configuration begins at runtime `+0x18`, initially empty name and ID `-1`. The real active update is conditional:

1. `createExtObject` calls `gcEnvironment::getEnablePartitionRollback` at `0x4be8bea4`
2. If enabled and actual filed model `+0xd78` is nonnull, virtual `+0x188` reads that selected configuration's ID and `+0x88` its actual name
3. `0x4be8bef3` calls `setConfigurationToLoad` with those values
4. A newly shared object receives the same candidate configuration at `0x4be96c60` under the same rollback condition

The selected Parasolid backend's fresh default is source-proven enabled: the public getter thunk `0x439d52f0` reaches a load of environment `+0x194` at `0x43e74610`; the selected backend singleton is returned by `sldgciParau::get` at `0x32f962c0`; its constructor writes `+0x194=1` at `0x32f95ccc`.

The mutable runtime setting can later change, so the constructor default is not a claim about every session. A generative model should explicitly retain the selected condition and actual active configuration, not confuse list index 0 with config ID 0 or force the embedded reference to remain empty.

The actual ID/name slots are independently recorded in [configuration-header construction](ConfigurationManagerHeader2026.md): ID `f08`, name `f18.f08`. This packet additionally pins the complete ID and name getter bodies.

## Construction scope and remaining acceptance

A model-derived construction can use:

1. Actual generated model and its distinct self-unit clones, with the existing standalone archive map
2. The explicit standalone wire context to emit a null component owner and zero local-unit suffix
3. Actual modeled feature ID and creation epoch for the owned surface FR
4. Actual generated file identity, active configuration and rollback condition for the live external reference
5. Actual shared list state for `IndexInRefList`; first fresh entry 0 follows the counter rule, not a donor value

Every participating object still needs its real surrounding fields, aliases, archive declarations and topology. This source checkpoint does not supply missing f48/f60 rows, surface identity representation, history or loader attachment state by guessing. It does not change any prior native warning receipt or establish application usability. Full native loading and edit/save/reopen with controls remain root-owned work.

## Reproduction

Run [VerifyLocalOwnerSources.py](../../tooling/sw2026/downstream/VerifyLocalOwnerSources.py) with `--bin-directory` naming the licensed external modules, `--record` naming the JSON record and an unused `--output` path. It verifies whole-module and source-interval hashes plus actual vtable targets. It performs no vendor execution or CAD parsing.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and complete [RE playbook](../../Playbook/README.md) apply before construction or native qualification.
