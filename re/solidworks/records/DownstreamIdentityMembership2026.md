# Downstream identity and entity-input membership in SOLIDWORKS 2026

**The populated `f40` vector is an ordered set of cloned native entity-id representations, not a fixed empty constructor value or one entry per face.** The actual fresh create route first collects body face/edge ids, then constructs and fills the downstream cache, then transfers the collector vector into `f40`. This is source proof, not native cache acceptance.

Task `B04-SW2026-DOWNSTREAM-MEMBERSHIP`, owner `flag_ownership`, delivery PR #121. Root owns the oracle, SDK integration and publication. Dependencies are the existing [body grammar](DownstreamIdArchiveGrammar2026.md), [standalone maps](DownstreamStandaloneMaps2026.md), [store route](DownstreamStandaloneStore2026.md) and [fresh reference assignments](DownstreamFreshReferenceAssignments2026.md). The exit for this checkpoint is pinned producer/selection/dedup knowledge with model-specific and runtime boundaries retained.

## Source authority

The [numeric ledger](DownstreamIdentityMembership2026.json) rechecks 32 complete function entries, including 34 declared unwind fragments, ten instruction windows and twelve exact RTTI-bound vtable cells. A separately identified update-method parent is hashed but only its identity-repair window was reviewed. Complete parent bounds are not claims that every branch in that update method is mapped.

All three unchanged originals have file version `34.5.2.604`, PE machine `0x8664`:

| Module | SHA-256 | Preferred base |
| --- | --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000` |
| `sldutu.dll` | `dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933` | `0x3cf80000` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` | `0x43740000` |

Original bytes were inspected statelessly with Apple LLVM 21. Bounds use the declared exception directory and its complete chained groups; small leaves end at a reviewed return or tail jump. No Hopper/REA target was opened, and no native function, application, schema, codec or test was executed. No CAD payload, held-out input or vendor listing is enclosed.

## The actual fresh route

`moModel_c::createDownstreamIdData`, `[0x4b578680,0x4b5788a5)`, SHA-256 `79313b4a2c0693d269b567e4c5f49df89645b38bde0d802ba35303922c86156b`, requires enabled downstream caching, null collector global `0x4db5dd18`, the selected viewer/lightweight gate and no rollback.

At `0x4b578745` it constructs actual `moBatchEntRefHelper_c(model,1)`. RTTI binds its primary table `0x4ce16a78`, locator `0x4d302788` and type descriptor `0x4db20c90`. The base constructor allocates a new empty entity-data-key tree at global `0x4db56280` and zeroes `c0/c4`; this is not inherited key coverage from a previous conversion. The derived constructor allocates an empty 24-byte vector descriptor at `+0x1b0` and stores the supplied `1` at `+0x250` on successful allocation.

The create scope saves global `0x4db592c0`, temporarily sets it to one, and later restores it. Another scope publishes the actual collector at `0x4db5dd18` and clears it at exit. These are runtime construction contexts, not wire flags or portable runtime dependencies.

At `0x4b57876e`, collector `0x4b519360` calls `createFaceEdgeIdMaps` before the downstream object is allocated. Prefix collection must then succeed. After constructor/prefix setup, `0x4b578824` calls cache population `0x4b5263c0`. At `0x4b578831`, leaf `[0x4b519e80,0x4b519e96)` writes collector `+0x1b0` to the out-pointer `cache+0x40` and clears the collector pointer. The cache is published at actual model `+0x1348`.

The earlier cache-constructor facts remain valid: `f30` empty, `f38=0`, `f40=NULL`. They are a different lifecycle point from this populated create route.

## Body selection and ordering

Both collector and cache preparation call `[0x4b538110,0x4b538406)`. Actual `moPart_c` table `0x4d1252d8` has `+0x1a0` true and `+0x1a8` false. Its selected part branch requires an initially empty output array, no rollback, runtime model `+0x161c==0` and actual atom manager `+0xd88` nonnull. The name of `+0x161c` is not inferred here.

The branch saves `SldDocMan::getEnableGetBodiesCache`, temporarily disables it, calls actual `moAtomManager::getBodies` at `0x4bcf3170`, and restores the previous Boolean. The raw arguments after the output array are `(0,0,NULL,1,0,0)`. The report does not rename those enum values without another proof.

Within the returned body order, `[0x4b512b00,0x4b512d6c)` processes:

1. All faces using actual `gcBody_w::getFirstFace` and `gcFace_w::getNextInBody`
2. Each face's `getMultiSurfaceId(wanted=0, feature=NULL, extra=NULL)` result order
3. All edges using `gcBody_w::getFirstEdge` and `gcEdge_w::getNextInBody`
4. Each edge's `getMultiEdgeId(0)` result order

These orderings precede the next selected body. Surface wanted-type zero is bound to actual `gcFaceIdAttrib_w::getAllFromEntity`; temporary attributes use the different wanted-type-one branch. Edge collection uses actual `gcEdgeIdAttrib_w::getAllFromEntity`. The collector's initial sums of body face/edge attribute counts are capacity planning, not the final emitted `f40` count.

No analytic cap/side/edge sort is performed by this collector. A physical cap-first order still depends on the actual kernel/body/attribute traversal. The static rule does not promote an order observed in another saved file.

## Membership and deduplication

Helper `[0x4b513ff0,0x4b514539)`, SHA-256 `67a9d82594028569772c5dd2a679bcc9d91cd61746f7c3557d2e4d8e43bce0a8`, processes each nonnull id representation in the returned native lists. It asks the registered geometry id helper for a `gcEntityIdDataStruct_c` key and compares that key in the newly allocated tree.

| Key branch | Actual action |
| --- | --- |
| Existing equivalent key, `0x4b514229..0x4b514270` | Update retained index/entity mappings through collector slots `+0xa0/+0x90`; no second slot-`+0x98` append |
| New key, `0x4b5142bf..0x4b51431c` | Retain the entity-data key, call slot `+0x98`, then register the new vector index |

Concrete collector `+0x98` is `[0x4b517d20,0x4b517f31)`, SHA-256 `a56a25d312ba29081869c86dd1649d61e55bb7b828190c3aad0cb81af8f61e71`. Fresh `+0x250=1` bypasses the older cached-reuse branch. It asks the actual original id representation's virtual `+0x280` for a concrete clone, retains it and appends its pointer. The face/edge category counters increment for that newly accepted key.

Therefore vector positions follow **first accepted comparable key**, across all selected faces and edges. `f40` is not a feature list, face count, raw attribute count or unconditionally one record per native entity. Existing multiple attribute histories remain inputs. The code does not replace an older real source feature reference with the current last feature merely because it is building a new downstream cache.

The comparator `[0x4b511a80,0x4b511c45)` compares integer/object counts, integer values and relevant actual external-owner identities/timestamps. It includes unset-time equivalence and a kind-40 negative-contour exception. It is not `memcmp`, raw pointer equality or an exact saved tuple comparison. The callback and comparator hashes, not a simplified set implementation, are the retained specification.

## Ordinary extrusion key vocabulary

The bound `moEntityIdHelper_c` slot-zero callback `[0x4c6c32e0,0x4c6c32fb)` forwards a nonnull actual id representation to its virtual `+0xd0`. The complete ordinary subtype callbacks give:

| Native class | Integer key | Object key |
| --- | --- | --- |
| `moFromSktEntSurfIdRep_c`, `0x4c6c8030` | `[74, FR+10, FR+18, FR+20 & ~0x10, permanent_marker]` | One actual `moFR::getXModel` result |
| `moEndFaceSurfIdRep_c`, `0x4c6c78a0` | `[40, FR+10, FR+18, FR+20 & ~0x10, cap_selector, contour]` | One actual `moFR::getXModel` result |

`FR+10` is the original feature identity; `FR+18` is its creation-time word. Negative cap contour is canonicalized to `-1` by the key callback, including a write to that source member. A missing FR produces zero integer/object counts. These callbacks bind declared format vocabulary and model-derived inputs, not captured row values.

The clone callbacks are independently RTTI-bound: cap `0x4c6cf810`, side `0x4c6cfbe0`. They invoke their actual constructor/copy chains. **The original owner in the dedup key and the copied `f40` keeper/FR/external graph are distinct ownership questions.** This checkpoint does not assert that the copied external object, runtime owner pointer or archive index aliases the original. Parent's separately bound FR/ExtObject copy proof owns that behavior. The cap clone also has old-version/global/feature contour compatibility branches, so a generic raw field copy is not justified by the word “clone”.

For a bare ordinary extrusion whose real kernel attributes are the expected cap and sketch-side representations, those real identities participate in this mechanism. A complete numerical membership/count/order still requires its actual edge-id attribute/subclass closure, body/attribute order and applicable clone contexts. No constant `f40=[]`, no face-count formula and no saved cap/lateral order is promoted.

## `f30`: UUID text

Cache preparation `[0x4b52cfd0,0x4b52d053)` requires an actual part/assembly owner and returns the selected body count. When that count is nonzero, initial population checks the actual string length. Empty `f30` calls exported `sldutu!GetSWGUID`, `[0x3d036390,0x3d03642f)`, SHA-256 `b66b11177e31e7635d5b4a66314ee48caecc032b2e78e7cf813a7fb2105b1dda`.

That function allocates a 40-byte narrow buffer, calls actual `RPCRT4!UuidCreate`, calls `UuidToStringA`, copies through the terminating NUL on successful conversion and releases the RPC-owned string. The cache assigns the result to its wide CString through the actual imported overload. No native RPC call was executed here, no saved UUID was read, and allocation/RPC failure behavior is not qualified.

This is per-cache bookkeeping, separate from persistent feature/node allocation. It is not an authenticated-vendor signature field in the inspected body.

## `f38`: polynomial lookup key

When initial `f38` is zero, exported `ut_64BitHashCString`, `[0x3cfa0440,0x3cfa047a)`, calls `[0x3cf9fe60,0x3cf9ff05)` twice. For ordered 16-bit code units returned at valid wide-CString indices, the selected positive bases yield:

`H_b(s) = sum(s[i] * b^i) mod 1,000,000,009`

`f38 = (uint64(H_32771(f30)) << 32) | H_32779(f30)`

The inner loop starts with hash zero and weight one, updates both using the actual base, and performs the unsigned reciprocal reductions by `0x3b9aca09`. Arguments `0x8003/0x800b` are multiplication bases in this body; no CryptoAPI operation occurs. The character accessor is imported as MFC ordinal 4913, and its external body is not newly recovered here.

This key registers an actual model handle in the native lookup map. It is not the persistent node counter. Independently chosen valid source bookkeeping plus the proven arithmetic is the construction direction; copying a saved UUID/key pair is not.

The separate update-method window calls `[0x4b52cec0,0x4b52cf0a)` if either string or key is absent. That helper fills an empty string and/or zero key individually. If both are present, the inspected branch does not recompute their agreement. This is not a claim of a universal loader integrity check or full update semantics.

## Evidence limits and next boundary

Confirmed static facts are the fresh collector/tree/vector allocation, actual face-before-edge traversal, new-key append branch, concrete clone dispatch, identity seeding and packed hash arithmetic. Actual copied reference ownership remains separately sourced. The complete ordinary extrusion edge-id subtype graph and its kernel/attribute order are still required before claiming an exact fresh `f40` graph. Later cache-population callbacks are not given a global preservation claim by this bounded checkpoint.

No matching saved standalone downstream source was parsed, no SDK source changed and no writer was implemented. Native loading, edit/save/reopen, generalization and usability remain unmeasured here. The packet preserves all earlier constructor, grammar, map and save evidence unchanged.

The governing [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and [full RE playbook](../../Playbook/README.md), including phase B, remain mandatory. Their stopping conditions are: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This is a bounded source checkpoint, not completion of the conversion goal. This lane has no oracle; native measurements must be requested from root.
