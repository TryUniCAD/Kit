# Selected extrusion ends and distance-display lifecycle in SOLIDWORKS 2026

The exact-build source binds internal surface type 4, selected reference publication and selected-line direction mode. Constructor, managed update and native dialog application have separate display lifecycles. The public `swEndCondUpToSelection=10` translation remains open.

Task `B04-SW2026-FREECAD-CYLINDER` remains owned by `/root/assembly_occurrence` for this source analysis, with `/root` owning integration and the oracle. Delivery is PR #121. Dependencies are the [five-driver lowering proposal](FreecadCylinderFiveDriverLowering2026.md), the [persistent direction wire](FreecadCylinderDirectionWire2026.md), the shared [end-condition construction](EndConditionConstruction2026.md), and new independently authored selected-end source locks before writer work. The exit remains complete C1–C11 acceptance for the source-preserving primitive; this checkpoint meets no native acceptance gate.

## Pinned authority and replay

The [numeric knowledge](FreecadCylinderSelectedEnd2026.json), [source-only collector](../../tooling/sw2026/freecad_cylinder/PinCylinderSelectedEnd.py) and [replay receipt](../measurements/2026/FreecadCylinderSelectedEnd01.json) bind these findings. Only identities, addresses, tokens, graph edges and independently authored rules are emitted. Licensed binaries and private instruction listings are not included.

| Original module    | SHA-256                                                            | Role                                            |
| ------------------ | ------------------------------------------------------------------ | ----------------------------------------------- |
| `sldmodu.dll`      | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | Native field and dimension owners               |
| `sldcoreu.dll`     | `3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3` | Actual mixed-mode managed extrusion packets     |
| `slduiu.dll`       | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` | Native command and end-dialog data application  |
| `sldappu.dll`      | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` | Macro-data copying and COM interception wrapper |
| `sldbasegeomu.dll` | `206430acc09197ae9416446d56156f79fdb3aae9d615f32b771314a92a0ad36a` | Native extrusion command dimension application  |

The managed MVID is `3f9c2ded-9024-4b12-ac82-deb36cae1451`, with CLI flags `0x18`. The verifier decodes selected declared CIL and uses the complete export table for native imports. Scope is document version 19000 on build `34.5.2.0604`.

```sh
uv run --no-project --offline --isolated --python 3.11 --with dnfile==0.18.0 --with dncil==1.0.2 --with pefile==2024.8.26 python -B /path/to/Kit/re/tooling/sw2026/freecad_cylinder/PinCylinderSelectedEnd.py --root /path/to/Kit --inputs /path/to/licensed/bin --knowledge /path/to/Kit/re/solidworks/records/FreecadCylinderSelectedEnd2026.json --output /new/selected-end/Pin.json
```

The input directory is read only for the five named originals. No CAD files, source specifications or native observations are inputs to this collector. Its output must be new. The receipt records the exact source dependencies, parser versions and complete chained native function ranges. It rejects a module hash mismatch or a document version other than 19000.

## Internal end publication

The listed tokens belong to the concrete extrusion packet classes.

| Owner and method                   | Managed token / RVA                                 | Independently decoded publication                                                                                                                                                          |
| ---------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ToSurfaceEndSpec_c.ApplyToModel` | `0x0600507e` / `0x142628` | Applies the base state, clones the actual surface wrapper through `+0x258`, calls `setISurfRef` with the actual end and clear flag 1, then sets type 4. |
| `ToSurfaceEndSpec_c.LoadFromModel` | `0x0600507d` / `0x1425f0`                           | Retrieves the actual end's `getISurfRef(end)` and constructs its managed surface wrapper when non-null                                                                                     |
| `ToSurfaceEndSpec_c.ReleaseData` | `0x0600507c` / `0x141d18` | Clears the managed surface and calls `removeISurfRef(end)` at `0x4baf6f10` to clear `f28` or `f48`. |
| `ExtrusionPacket_c.CurrentEndSpec` | `0x0600503a` / `0x141848` | Native types 4, 3, 5 and 7 select surface, point, surface-offset and body end classes. |
| First/second packet setters        | `0x0600503d`, `0x0600503f` / `0x14190c`, `0x141944` | Bind actual end indices 0 and 1 respectively                                                                                                                                               |

`moEndSpec_c::setType` at `0x4b3100b0` stores the supplied integer in `f0c + 4*end`. Getter `0x4b30d800` returns that field. Display allocation and pruning have separate calls.

The surface method and base publish the reference and type. Blind `0x06005072` publishes a distance before type 0, and surface-offset `0x06005083` publishes a distance before type 5. Point `0x06005078`, mid-plane `0x0600508c` and body `0x06005089` set types 3, 6 and 7 respectively.

## Persistent selected-line direction

`EndSpecification_c.ApplyToModel`, token `0x0600506a`, RVA `0x1423c4`, destroys any prior direction object and, when an actual line wrapper exists, clones that wrapper and allocates a reference-backed `moDirectionSpec_c` with the authored flip and **mode 3**. Its native constructor import resolves to `sldmodu 0x4c302ac0`. The independent calculated vector used by the managed property representation is not passed as the persistent literal-vector member.

The already pinned native `getUpdatedDirection` at `0x4c3032a0` reads the actual geometry. Its branch at `0x4c303754` selects the normalized primary geometry when `((f14 - 3) & 0xfffffffb) == 0`, namely modes 3 or 7, then applies the independent `f10` reversal. This ties the managed ordinary selected-line route's `f14=3` to the native operation. It does not revise the earlier reference constructor's wider integer input domain or claim a selected-plane managed direction packet.

The managed load casts its direction to `moLineRef_w`. A limiting plane has a separate reference owner. The earlier wire record covers the native plane-direction route. [Persistent direction](FreecadCylinderDirectionWire2026.md)

## Distance-display lifecycle

| Stage                                 | Exact source authority                                                                                | State justified by that stage                                                                                                                                                                                            |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Fresh extrusion construction | `moExtrusion_c` at `0x4bad3ab0`, end constructor `0x4bad35c0` | Four initial distance and angular graphs use roles 1–4. The from-offset graph uses role 19. |
| Managed selected-surface update alone | Shared `0x0600506a` then concrete `0x0600507e` | Changes selected geometry and native type 4 while retaining the existing displays. |
| Native end-dialog complete apply | `uoESDlgData_c` table `0x4a59fee8`, slot `+0x138` to `0x493e5a80`, call `0x493e5f7e` | Publishes ordered types, references and draft state, then calls recreation and pruning with the actual model, feature and four values. |
| Native command dimension application | `sldbasegeomu 0x329423a0`, call `0x32942d54` | Has another direct path to the same recreation function. |
| Old-version load repair | Extrusion `SerializePass2` at `0x4bb241e0`, call `0x4bb243f6` | Invokes cleanup during load for source versions below `0x1c3`. |

The shared cleanup/recreation predicates were first recorded for [through-all construction](ThroughAllConstruction2026.md). They also include internal selected-surface type 4:

- First distance `f18`: prune when `1 <= unsigned(type[0]) <= 4` and environment selector `0x33` is false
- Second distance `f20`: prune when the feature is single-ended or its second type is in 1–4, under the same environment predicate
- Recreation iterates actual ends 0 and 1 and skips new distance allocation on this prune branch
- On the opposite branch, retain or allocate an actual distance display with role `end + 1`

`deleteNotUsedDims` removes the configuration data, destroys the display and nulls the owner. `recreateNecessaryDisplayDims` also destroys and clears the display on its prune branch. Both query the session environment slot `+0x78` with selector `0x33`. The selector's semantic name remains open.

Derive display ownership from the actual application path and environment predicate. The displays are archive object references. The initial construction roles belong to an earlier stage than subsequent display removal.

## Public enum translation boundary

The public contract assigns `swEndCondUpToSelection=10`. Its route to the internal end integer remains open. [Prior public-contract review](FreecadCylinderFiveDriverLowering2026.md)

The reached exact-build native path is narrower:

1. `auModelDoc_c::iApiFeatureExtrusion4` at `0x492546e0` calls `uoDData_c::loadFromMacro` at `0x49254a33`, then selected-data loading at `0x49254b04`
2. The actual data map has 23 rows. Ordered rows 3 and 4 are integer kind 4 at dialog offsets `0x84` and `0xb8`
3. `loadFromMacro` at `0x459ee330` copies the integer arguments through those rows without an enum conversion
4. The end-dialog apply method stores those ordered integers directly into actual native `f0c/f10`
5. `loadAdditionalData` at `0x493e6470` reaches selected-geometry branches for types 3, 4/5 and 7

The public `FeatureExtrusion3` wrapper at `0x4564bf70` forwards through virtual `+0x7a8`. The target implementation remains open, including any compatibility translation or newer command route.

## Actionable lowering and remaining proof

The source-grounded target path remains: circle/profile owner, two authored angled datum planes, their actual intersection-axis owner, a reference-backed direction with the proved selected-line mode, and an actual limit-plane surface wrapper on the chosen end. Internal type 4 and surface ownership now have a concrete publication path. The source vertical height still belongs to the limit plane's real offset driver; it is not an inactive extrusion depth parameter. See the earlier [five-driver construction proposal](FreecadCylinderFiveDriverLowering2026.md).

Before a new writer, a separate controlled native source protocol must bind the registered public selected-end route, actual direction geometry, native end integer, live display inventory before/after edit/save and independent geometry for the non-normal selected-plane limit. Both fresh and saved states matter. The source locks for normal circle ends, principal planes and offset planes do not qualify this combined family. Whole-sector `Angle` editing, oblique-driver histories and source metadata still require their existing independent gates.

The [gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Extrusion/SelectedSurfaceModeDoesNotPruneDistance.md) states the constructor/apply distinction. This checkpoint preserves the earlier frozen wire packet, contains no production changes and keeps all native and public writer acceptance flags false.
