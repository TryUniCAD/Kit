# Saved two-stock through-all ownership

This read-only audit advances `B04-SW2026-EXTRUDE-THROUGHALL` on PR #121. It inspects the 75,510-byte disclosed automatic-request original from packet 03, SHA-256 `748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3`. Its healthy native lifecycle retained the selected `SteadyStock` and the intact `MovingStock` through the actual 10 → 29 mm upstream edit. The independent named explicit API request returned null. [Native method and outcome](ThroughAllMultiStockScope2026.md#packet-03-native-result) · [Measured receipt](../measurements/2026/ThroughAllMultiStockScopeObserved01.json)

## Confirmed archive owners

Format 4, model version 19000 and configuration 0 passed the existing linked reader with complete schemas and zero provisional owners. Six streams re-emitted byte-exactly in memory. These include the `Contents/Config-0` graph at 25,378 bytes and `Contents/Config-0-ResolvedFeatures` at 20,625 bytes. [Archive entry](../../../src/convert/adapters/solidworks/Core/TypedResolved/ReadNativeLink.py) · [Scope wire fields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/BodyFields.py)

| Resolved feature | Class, schema, feature ID | `f810`, `f544` | Actual `f60` profile and support | End |
| --- | --- | --- | --- | --- |
| `SteadyStock` | `moExtrusion_c`, 1, 32 | −1, 0 | `SteadyProfile` 26, Front Plane 2 | Blind +Z, actual D1 12 mm, dimension ID 27 |
| `MovingStock` | `moICE_c`, 1, 40 | 0, 0 | `MovingProfile` 33, Right Plane 4 | Blind +X, actual D1 10 mm, dimension ID 34 |
| `ThroughFeature` | `moICE_c`, 1, 47 | 1, 1 | `ThroughProfile` 41, Front Plane 2 | `f818` one-end through-all, words `f08/f0c/f10/f88/f8c = 1/1/0/0/1`, null active distance owners |

The archive gives `MovingStock` its own output and no consumed input. The cut's wire sketch dependency is its own profile. Its selected stock dependency is recorded separately in the managed body graph.

| `Contents/Config-0` `moPart_c.fd88.atoms` slot | `moAtom_c` map index | Atom ID `f140` | Producer `f12c/f130` and actual `f528` alias | Actual `f530` consumer | `f144` |
| --- | ---: | ---: | --- | --- | ---: |
| 0 | 58 | 103 | 47 / `ThroughFeature` | none | 0 |
| 1 | 59 | 102 | 40 / `MovingStock` | none | 0 |
| 2 | 60 | 101 | 32 / `SteadyStock` | `ThroughFeature` | 1 |

The count `fd88.n6c` is 3 and `fd88.f260` is 103. The inherited map and the manager provide the same three actual objects. The cut uses `f544=1`, `has_f548=1` and one wrapper in `f548.items[0].o`. The exact-build serializer has no operand for its separate runtime automatic-selection member `+0x558`. The saved scope describes the selected result of authoring. [Exact-build boundary](ThroughAllSelectedBodyConstruction2026.md#exact-build-evidence)

The wrapper is `moCompSolidBody_c` schema 1, map index 364 and offsets [19451,19749) in the linked resolved stream. It sets `f18=f1c=101`, `f108=32` and `n110=1, f110=[101]`. Its `f58` is `moUnitComponent_c` index 365, `has_ext=0`, with `owner` object-identical to Config-0's `moPart_c` index 2. Its `ff0` is a live `moFaceRef_c` at index 366, offsets [19559,19729). The wrapper's observed kernel words are `f100=90, f104=103`.

The carrier's six `ff0.f10` slots contain five concrete representation objects and one null slot. Three `moFromSktEntSurfIdRep_c.f38` sketch markers are 4, 1 and 3. Two `moEndFaceSurfIdRep_c.f38` cap selectors are 0 and 1. All five `rep.f10.f10` objects are `moFR_c` and resolve through `moFR_c.f10.f00=32`. Their `moFR_c.f08` edges alias one `moExtObject_c` schema 1, map index 237. All ten matching references beneath `SteadyStock.f4a8.f48.items[0].o.f08` alias that exact object. `ThroughFeature.f4c0.f68` aliases the actual cut. These identities bind the selected carrier to `SteadyStock` independently of matching integer atom keys. [Wrapper grammar](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ComponentFields.py#L269) · [Permanent markers and cap selectors](DownstreamIdentityMembership2026.md)

## First unsupported semantic owners

Public read reaches `ReadCutHistory` and refuses with `multiple operation histories are outside typed blind topology`. Its fallback returns one design body, describes `MovingStock` as a join of `SteadyStock`, assigns the cut to `MovingStock` and provides no cut body selection. The typed archive gives the correct owners. A focused read of `MovingStock` also reaches the non-cut extrusion reader's concrete `moExtrusion_c` restriction. At the next graph boundary the managed atom reader accepts the three atoms, but the saved cut helper requires the complete manager to be exactly its input and output pair. The saved scope helper independently requires the stock scope word to equal the cut scope word. The saved wrapper identity check accepts this wrapper's producer and component bindings. Its cold branch refuses the observed face and kernel words. [First history refusal](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/ReadCutHistory.py#L35) · [Concrete extrusion class](../../../src/convert/adapters/solidworks/Core/TypedResolved/ReadExtrude.py#L20) · [Atom pair guard](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/ReadSavedCutBodies.py#L31) · [Scope guard](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/CheckSavedCutScope.py#L17)

The first generation prerequisite is actual independent-stock ownership in a neutral preparation. The existing `BooleanOp.KCreate`, ordinary blind feature with its own sketch and D1, and a distinct `DesignBody(final_feature_id=MovingStock)` can express the unconsumed result. The cut needs the separate feature-body selection of `SteadyStock` and its own result body. The existing through-all source projector only accepts one stock followed by one cut. The writer specification also requires the selected stock and tool to share the enclosed-circle regime. This sample is a side-opening circular notch. [Neutral operation and final body types](../../../src/interchange/Enums/EnumFeatures.py#L53) · [Source operation gate](../../../src/convert/adapters/solidworks/Core/Preparation/ThroughAll/Source/ReadSourceOps.py#L24) · [Writer scope and geometry gates](../../../src/convert/adapters/solidworks/Archive/Construction/ThroughAll/ProjectThroughPart.py#L54) · [Circle containment guard](../../../src/convert/adapters/solidworks/Archive/Construction/ThroughAll/ThroughPartSpec.py#L54)

Start with independently generated disjoint blind producers, signed supports and two body ownership paths. Then bind the selected input and separate cut output while keeping the other producer intact. The current body wrapper generator uses the one-solid route with `ff0=None, f100=f104=0`. Reproducing the saved face-bearing graph requires generating stable carrier identities and deriving its kernel words. This one save confirms the presence and aliasing of the face carrier. A separate controlled cold trial must establish whether multibody regeneration accepts a neutral carrier or neutral kernel words. [Current one-stock constructor](../../../src/convert/adapters/solidworks/Archive/Construction/BodyScope/MakeBodyRef.py#L13) · [Qualified single-solid lookup](ThroughAllSelectedBodyConstruction2026.md#exact-build-evidence)

## Independent extraction

The [audit](../../tooling/sw2026/throughsource/AuditThroughMultiStockSaved.py) has SHA-256 `7dbfd440ebdb2c52facf40656b445f5ed38f55214c882433d72b88f877b32181`. It gave identical numeric, typed and digest-only output with isolated reader `e1282e125905c849254f4726099efc6cf25c3cb9` and exact aggregate `9f0ccb5389c121e750ca3b73f8e5d248b34d2e15`. The [tracked output](../measurements/2026/ThroughAllMultiStockArchive01.json) has SHA-256 `f98b7369b9ecffbd58566f2701e79fa3064327f864faf97fd9b06abf65ebd540`. Run from the research worktree to reproduce the aggregate extraction.

```sh
revision=9f0ccb5389c121e750ca3b73f8e5d248b34d2e15
scratch="$(mktemp -d /tmp/KitMultiStockTypedRead.XXXXXXXX)"
source_path='/Users/odin/Documents/UniCAD/Oracle121Takeover/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT'
git archive "$revision" -- src | tar -xf - -C "$scratch"
mkdir -p "$scratch/re/tooling/sw2026"
git show "$revision:re/tooling/sw2026/AuditThroughAllDisclosed.py" \
  > "$scratch/re/tooling/sw2026/AuditThroughAllDisclosed.py"
python3.14 -I -B re/tooling/sw2026/throughsource/AuditThroughMultiStockSaved.py \
  --source "$source_path" --sdk-root "$scratch" > "$scratch/Receipt.json"
shasum -a 256 "$scratch/Receipt.json"
```

This audit produces zero native files. It adds zero held-out, production and corpus acceptance credit.

## Exact unrestricted contrast

The native unrestricted control changed the cut request to `UseFeatScope=False, UseAutoSelect=False`. Its exact source SHA-256 is `f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22`. The initial saved geometry and body ownership match the prior automatic-request source. In both cases the cut consumes atom 101 from map slot 60, emits atom 103 at slot 58 and leaves atom 102 at slot 59. The operation order marks are −1, 0 and 1. [Unrestricted native result](ThroughAllMultiStockScope2026.md#unrestricted-scope-contrast)

The resolved selection stores `f544=1`, `has_f548=1` and the actual wrapper. The unrestricted save stores `f544=0`, `has_f548=0` and no wrapper. Both resolved streams have 20,625 uncompressed bytes. The physical comparison follows the typed owners and fields because total stream size cannot identify the scope. The independent native edit distinguishes the two saved models. Only unrestricted scope cuts the moving stock that initially missed the tool.

The [comparison worker](../../tooling/sw2026/throughsource/CompareSavedStockScope.py) read both exact disclosed trees. Two fresh processes gave byte-identical reports. Each source retained its original file digest, and each re-emitted all six linked streams exactly in memory. No native file was emitted. [Exact structural receipt](../measurements/2026/ThroughAllSavedScopeContrast01.json)
