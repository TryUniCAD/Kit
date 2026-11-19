# Ordinary downstream body representatives, SOLIDWORKS 2026

The pinned source maps optional `f90` body construction, the representative face, the backing atom list and the final store fields. Complete native qualification remains open. [Evidence vocabulary](../../Playbook/Evidence.md)

Task `B04-SW2026-DOWNSTREAM-BODY-REPRESENTATIVE`, owner `configuration_header`, delivery PR #121. Root owns generated model/kernel identities, shared codec integration and native oracle. The exit condition is a hash-verifiable conditional construction rule, including unresolved runtime dependencies. [Numeric ledger](DownstreamBodyRepresentative2026.json) · [Source receipt](../measurements/2026/DownstreamBodyRepresentativeSource01.json)

The ledger pins 30 complete functions, 60 source intervals, seven concrete virtual slots and 21 typed imports across four originals:

| Original | SHA256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` |
| `sldgciParau.dll` | `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce` |
| `PSKERNEL.dll` 37.01.250 | `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969` |

No original module, instruction listing, CAD data, capture-derived field row or case-specific output is enclosed.

## Actual creation gate and arguments

Fresh orchestration at `0x4b526633..0x4b526714` requires actual part `+0x1a0` true, runtime option `0x4db5681c & 0x10`, nonempty retained body inventory, part `+0x1a8` false and actual `body.isSolid(0,0)`. The runtime option's selected value remains open.

Creator `0x4b7e8980` receives the model's actual self component and body atom, with null face and explicit-body inputs. Its final stack word is native constructor plumbing. The appender separately receives the actual inventory body.

The constructor copies the atom ID to `f18/f1c`. The component model supplies `fd88`, and `getAtomFromId` at `0x4bcf2ea0` resolves the atom whose `f160` holds the live body. The standalone `moUnitComponent_c +0x1e8` returns false and skips component-body re-enumeration. [Local owner](DownstreamLocalOwnerContext2026.md)

Base constructor `0x4b2786c0` starts with null representative `+0xf0` (wire `ff0`), null runtime face `+0xf8`, zero `f100/f104`, `f108=-1`, and an empty backing `su_CUIntArray`.

## Model state, history and actual representative face

Actual part `+0x1250(0)` calls `moModel::isViewerModel` at `0x4c02d7d0`. Model `f2b0` bit `0x4` clear takes the viewer branch, which may retain `f108=-1` and select the body's first face directly.

In the selected non-viewer one-boss graph:

1. Resolve the starting atom and call `getBaseAtom` at `0x4bcf2f80`.
2. Take the returned atom's actual producing feature at `f150`.
3. Set body-reference `f108` from feature virtual `+0x188`. The actual extrusion table binds that slot to `0x4b283ba0`, which reads feature **`f08`**.
4. Collect a representative through `0x4b7061a0`. The proved rollback-enabled branch scans `getFirstFace` and `getNextInBody`, stopping at the first accepted face.
5. If the primary feature supplies no face, a separately returned alternate feature can be tried. It overwrites `f108` only after a nonempty match list. If neither succeeds, actual body `getFirstFace` is the fallback.

Face acceptance at `0x4b714dc0` reads the actual face-ID attributes. It builds each FR from integer field 2 indexes 1 through 3 for feature ID, time and flags, plus pointer field 1 index 0 for the external owner. It calls `moFR::isSame` and requires a nonempty collection with every owner matching. The separate out flag can indicate a single matching attribute.

A one-boss prism with one matching FR per face selects the first actual shell face. Rollback-disabled selection, mixed owners and alternate features follow their own branches.

### First/next order reaches actual kernel links

The exact wrappers are:

| API | Model-facing wrapper | Backend | Kernel |
| --- | --- | --- | --- |
| First face | `sldgcu!0x43890080` via `0x43e83f70` | `sldgciParau!0x32fd98e0` | `PK_BODY_ask_first_face`, `0x1800f4be0` |
| Next face | `sldgcu!0x439ec580` via `0x43e850c0` | `sldgciParau!0x330227c0` | `PK_FACE_ask_next_in_body`, `0x18025a280` |

The plain kernel branch starts at actual BODY region `+0x100`, REGION shell `+0x28` and SHELL face `+0x20`, skipping empty links. It advances FACE next `+0x48`, then later shells/regions through their `+0x18` links. The [existing field registration and traversal proof](ParasolidBodyTraversal2026.md) binds those named owners. Actual tag projection remains separate from portable indices or node identity. Filtered/faceted/grouped contexts are outside this plain one-shell conclusion.

## Backing IDs come from atom history

`getBaseAtom` appends the starting actual atom to its supplied collection **before** traversing its feature's atom-list relations. It collects each visited predecessor in order with native feature-cycle protection. The body constructor then extracts each collected atom's `f140` and assigns those IDs to its backing unsigned array.

For a single boss with empty `f530` inputs, traversal stops at the actual starting atom. The backing list contains that atom's ID, and the boss is the base producing feature. Multiple outputs and dependent histories require walking their actual atom graph.

## The representative reference is a new owner

Helper `0x4b802f40` uses the selected actual face to find its real `f48` CompFace. It creates a new FaceRef through `0x4b74cb00`, installs it at body `+0xf0` and explicitly inserts role0 with the selected actual face's allocated downstream ID.

Copy mode 0 creates fresh inline wrappers with the original representation aliases. The copy starts without the source `f18` and live `f70` handle. Installing role 0 allocates a separate embedded owner. [Stored face rules](DownstreamStoredFaceState2026.md)

When no copy is available, the constructor requests `FaceRef.get(actual face, actual component filed owner,0)`. It retains the actual face at runtime `+0xf8`. Runtime reference use counts are separate from the wire fields.

## Conditional registration and packed clock

Appender `0x4b524ba0` requires nonnull runtime body vector `f708`, nonnull representative at `+0xf0`, positive inline count and real array, actual downstream role data, and role0 resolving through signed map → `f340` identity info → checked `f6d8` actual face. A semantically empty wrapper cannot register.

Registration consumes and increments data `f08`, appends the component and allocated ID to `f90`, and appends the actual inventory body to `f708`. Earlier face, edge and optional vertex allocations determine the body ID.

| New `f400` identity-info operand | Source-derived value |
| --- | --- |
| `+0x08` | **Current `f48.size()`**, computed at `0x4b524c28..0x4b524c30`, stored at `0x4b524ceb` |
| `+0x0c` | Actual inventory body `getAtomId()` |
| `+0x10` | Role0-resolved actual face `getId()` node ID |
| Packed `+0x14` | Exact qword from data `+0xbd0`, loaded at `0x4b524cb8`, stored at `0x4b524cf6` |

The packed clock comes from the construction FILETIME sampled at `0x4b526478` before faces and edges. Registration returns `f90.size()-1` as the body ordinal while `f400 +0x08` takes the current face count. [Construction clock](DownstreamFaceRegistration2026.md)

After append, body `setDownstreamId` receives the allocated number, shared clock, ordinary zero discriminator, data `f38` key and null optional attribute owners.

## Final ordinary store normalizes both identity words

The shared serializer at `0x4bba4390` is reached from CompSolidBody's tail jump at `0x4bba6b10`. Version 19000 writes the CompRef base, typed FaceRef `+0xf0`, backing count and words, then `f108`, `f104` and `f100`.

At `0x4bba444f`, a **qword** zero at `+0x100` clears **both** adjacent i32 fields `f100` and `f104`. With condition `0x80` clear and a valid retained `+0xf8` face, it repopulates `f100` from that actual face. Only a nonnull valid actual body of that face repopulates `f104` from its atom ID. Skipped or invalid branches retain the applicable zero words. Constructor atom copies in inherited `f18/f1c` are separate and do not supply this tail.

The serializer retains the actual representative, backing history IDs and `f108`. [Existing standalone body codec](DownstreamStandaloneBodyCodec2026.md)

## Evidence and remaining obligations

Run the verifier with the original `--bin-directory`, licensed `--kernel`, this `--record` and unused `--output`. It authenticates original source intervals and dispatch cells. [Source verifier](../../tooling/sw2026/downstream/VerifyBodyRepresentativeSources.py)

Still open are actual option policy/value, live tag/wrapper allocation and validity, broader histories/alternate owners, temporary map lifetime and nonordinary contexts. This tranche reads zero CAD or held-out inputs, performs zero VM calls or SDK/native product runs, changes no shared source, and opens no REA/Hopper target. Generated cache load/rebuild/save and warning32 remain unqualified. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and full [RE playbook](../../Playbook/README.md) apply before advancing.
