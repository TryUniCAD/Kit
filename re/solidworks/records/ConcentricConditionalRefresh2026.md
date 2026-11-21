# Conditional concentric orientation refresh in SOLIDWORKS 2026

Mandatory cold-open scheduling is still unproved. This exact-build static checkpoint establishes a conditional ordinary concentric map-to-cylinder getter path and explains why its change-check method does not prove preservation of the optional orientation state.

Task `B04-SW2026-MATES-CONCENTRIC`; owner `/root/flag_ownership`; delivery PR #121. Dependencies are [the selected-face enable record](ConcentricOrientationEnable2026.md), the actual [concentric archive ownership](ConcentricMateArchive2026.md), and [the disclosed ordinary source scope](ConcentricMateConstructionSources2026.md). Exit for this checkpoint is an actual concrete map, ordinary-branch dispatch, wrapper alias, exact readiness guards and side-effect boundary. The upstream cold-open caller and fresh writer acceptance remain separate work.

## Identity and evidence

All addresses refer to original x64 `sldmodu.dll`, release `34.5.2.0604`, preferred base `0x4b140000`, 46,536,280 bytes, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

The authoritative image digest is recorded without abbreviation in [the numeric evidence](ConcentricConditionalRefresh2026.json). That record retains 11 full functions or leaves, ten complete unwind fragments, 11 instruction windows, nine direct call instructions, three concrete primary RTTI tables and six virtual cells. Original-PE metadata and LLVM instruction boundaries were checked; proprietary listings stay outside the checkout. No CAD, COM, VM, schema, codec or product tests were run. No sealed inputs or source CAD payloads were opened. Existing disclosed knowledge records supply the ordinary source position enum; no captured field is used to construct an output.

## Actual ordinary owner and alias

The concrete `moConcentricMateMap_c` primary table is `0x4cfe9190`, complete-object locator `0x4d33b458`, type descriptor `0x4db38038`. Its virtual `+0xb0` points to `[0x4bcc8090,0x4bcc81b9)`, SHA-256 `e753db42293c01609cbd6931be8a0760c8f0da9d61cca0386836810e27c13c0e`.

The actual mate at runtime map `+0x28` is examined first. Ordinary position `f4c4=-1` takes the common helper `0x4bcca300` at call `0x4bcc812d`. The separate direct cylinder-pair helper `0x4bcc22f0` is reached by a misalignment branch. The six disclosed ordinary source states are already documented with `f4c4=-1`; the misalignment-only helper must not be used to explain their ordinary refresh.

The common helper occupies `[0x4bcca300,0x4bcca47d)`, SHA-256 `5e31feeb4b0f2f74bd70f8a93aba9981daf959b73bf80e5d989dda2345ba0ee8`. Its first 57-byte unwind fragment is not its full body: all three contiguous fragments are retained. It loops the actual mate endpoint count and selects each actual endpoint through concrete mate virtuals:

| Receiver | Slot | Actual target | Proven owner |
| --- | --- | --- | --- |
| `moMateConcentric` table `0x4cfa8fb0` | `+0x1ef8` | `[0x4b289870,0x4b289877)` | Read runtime mate `+0x420` endpoint count |
| Same actual mate | `+0x1f00` | `[0x4bc44ed0,0x4bc44edf)` | Return runtime mate `+0x410[ordinal]` wrapper |
| Actual `moCylinderRef_w` table `0x4cd938c0` | `+0x260` | `[0x4c310580,0x4c310618)` | `moRefWrapper_c::dataHasChanged` |
| Same actual cylinder wrapper | `+0x3c0` | `[0x4c323b70,0x4c323f22)` | Concrete cylinder change check |

Runtime map `+0x10`, wrapper `+0x10` and mate fields belong to different receivers. No shared-offset meaning is implied.

## Exact conditional getter path

The common helper invokes wrapper `+0x260` when both conditions hold:

- Runtime persistence options bit 2 is clear.
- Runtime map `+0x10` equals zero.

The call at `0x4bcca38c` passes option zero, null optional output pointers and force zero. `moAssembly_c::getPersistenceOptions` reads a runtime global at `0x4dacb0bc`; neither its observed value nor a fresh default is established here.

The base method requires runtime wrapper byte `+0x3c` to be zero. With force zero and the same-model predicate false, the external-context helper `0x4c310e30` must succeed before the concrete change check runs. The base then invokes the actual cylinder `+0x3c0` at `0x4c3105ed`.

The cylinder check requires runtime `+0x30` equal to zero, signed runtime `+0x20` no greater than zero, and `isLocked()` false. It then calls `moCylinderRef_w::getCylinder` at `0x4c323ccd`, using transform mode zero and an actual face-tag output pointer. The full concrete check hash is `8db54934af36847756c73899f851bcab9932aca27ab3889c15053f4d68fb4b1c`.

The getter's initial helper must return numeric status 1, 4 or 5 and runtime wrapper `+0x30` must remain zero before component-specific extraction. In the actual `moCompFace_c` branch it resolves `getFace(1,0,null,null)`, requires a real face and a supported native cylinder/cone extraction, and leaves the orientation-consumer skip flag zero. If that path reaches the post-transform block with private state `+0x108` present, the getter calls `0x4c309960` at `0x4c313f32`. The exact getter and consumer full-body hashes are retained in the numeric record and prior construction evidence.

## Restoration does not establish preservation

The concrete change check snapshots and restores world point `+0xd0`, world unit axis `+0xe8`, radius `+0x100`, selected base words `+0x08/+0x0c`, and the earlier transform presence/values at `+0x10/+0x18`. It does not snapshot and restore private orientation state `+0x108`. That state's local vector is the separate optional wire field established in the enable/serialization record.

Therefore this is not a pure observer merely because its world geometry is restored. A reached getter may update private orientation history through its actual consumer. No assertion that the local vector always changes, or always stays unchanged, follows from this call graph.

## Exact remaining boundary

The following are not proved by this checkpoint:

- Which current-version cold-open owner invokes actual concentric map `+0xb0` before solve, and with which effective runtime options/map readiness.
- Whether that invocation takes the conditional change check for the selected generated graph.
- The remaining common map entity transport through `+0x1a0`, `0x4bcc7be0` and `0x4bcb1d60`, including downstream helpers `0x4bcb1c30` and `0x4c6f5120`.
- Full orientation preservation across solver/owner/listener lifecycle or fresh native/held-out writer acceptance.

No whole-state default or cache-neutrality rule is added. The earlier generic assembly cache initializer still skips actual cylinders, and loaded optional state is still reconstructed by the serializer rather than by the UI enable caller.

The CAD stopping conditions remain “The first is success under every criterion on this page.” and “The second is the end of the available context.” This is an evidence checkpoint, not completion of the overall CAD goal. The next action is to bind the actual cold-open map invocation and its runtime guards, then the remaining entity transport side effects.
