# Binary display intent for generated concentric assemblies

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state`, owner `assembly_frontier`, delivery PR #121. The internal SDK now publishes the binary display owner for one generated, aligned and unlocked radial concentric pair. The ordinary no-intent assembly path retained its full disclosed baseline. The opt-in path regenerated the exact parent and child artifacts already measured by SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. This opens a bounded constructor prerequisite. Original source equivalence and public writer admission remain closed. [Native single-store discriminator](ConcentricRadialVisibilityDiscriminator2026.md#single-store-experiments) · [Native measurement](../measurements/2026/ConcentricRadialDisplayStoresNative01.json)

## Semantic input and wire owners

The existing `EmitAsmStreams` accepts optional `DisplayValues` containing three ordered `AsmDisplayIn` rows. The input supplies authored printable names and explicit Booleans keyed by the actual occurrence labels. It has no archive slots, file bytes, version words or captured values. The active configuration and both persistent component IDs are resolved from the assembled graph. The only scope currently admitted is the measured schema-one 19000 profile. [Assembly composition](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/EmitAsmStreams.py) · [Input contract](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Displays/AsmDisplayIn.py)

| Owner | Bound rule |
| --- | --- |
| Assembly scope | One actual selected configuration, empty generated CMgr locator, one shared generated forward radial child without a visual store, and two visible direct rigid occurrences. The first occurrence is fixed. The actual ordered selected cylinder faces join the aligned unlocked mate back to these occurrences. |
| State semantics | The measured `Display State-1` is all visible. Two printable ASCII authored names are distinct under case folding and own opposite one-visible/one-hidden vectors. Each row names both actual occurrences exactly once. |
| File and context | Matching actual Header owners supply the parent locator and title. New pooled string handles own both detached occurrence rows. The generated ordinary configuration paths must agree with their actual reference names, IDs and update stamps before the binary store derives its flag-zero contexts. |
| Planes | Three actual principal datums appear in reverse feature order. Their ordered creation-log owners must agree across both headers and be empty in this profile. The existing `DatumTime` getter computes the sentinel `2592000` from that empty state. |
| Visibility rows | One configuration association points to the all-visible state key. Store keys and counts follow the actual three state rows. The ordered contexts are reversed relative to the instance tree. The shared null visual properties, separate visible or hidden occurrence flags, default alias and plane flags retain the measured object identity and role vocabulary. |
| Serialization | The SDK shared `BodyWriter` constructs a separate base-one archive with condition mask `0x20004000` and the bounded schema-one layouts. Only the local detached external-feature path is admitted. Its actual null backlink and ordinary file owner are checked. The empty tracker branch writes its zero row count. |

The binary owner is the only additional stream. The SDK leaves `COMPINSTANCETREE` unchanged. In the measured native store-only arm, the target application applied both named states before save and wrote its own instance-tree representation after the edit. The separately measured XML-only arm could not publish the names. The normal SDK XML reader's policy is unchanged. [Save and reopen comparison](ConcentricRadialVisibilityDiscriminator2026.md) · [SDK display wire context](../../../src/convert/adapters/solidworks/Archive/VisualStates/WriteAsmVisual.py) · [Detached rows](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Displays/MakeVisContexts.py)

## Exact verification

The [guarded verifier](../../tooling/sw2026/para/concentric/VerifySdkVisualStore.py) binds the exact disclosed `RadialConcentricDisplay04` trial `ac2696da314b7e2d4939fd75664270acecfe0274a479eafb9c2c6d5440aaed4b` and native summary `11f45d064babbd34bc910c1d2ebc3c228e605ce572d9f9775d3a4b2ea6aef37e`. The earlier native run used five fresh processes, healthy controls and 168 numeric checks, including 84 candidate checks. The two initial files come from the original disclosed scalar and portable neutral intent at the exact same locators and epoch. The comparison opens disclosed frozen generation outputs only in the supervisor after worker execution. Runtime construction inside each fresh worker uses the shared SDK assembly and body codecs, and no research layout registry or stored native file bytes.

| Comparison | Measured result |
| --- | --- |
| No-intent full parent | `31096319f1bcf8e949662e406a74ccb7e5bda27643c63352ddff27d5920c045f`, exactly the complete native baseline |
| Opt-in full parent | `55d998baba269aba1513fc599ffd08e7aaa44f0577ac5fd8da673f8eb4f9488d`, exactly the fully measured store-only artifact |
| Shared child | `b877a05784e23ae16c49e5ee74d01cc31ba62a87a24b21780c1327934c352970` in both arms |
| Added stream | `3556fa8cf4543aea6f57108b5e1c5c33eb423e70e73ce373dfa6d445ffb5d163`, 1,819 bytes, terminal map 39, complete independent typed exact replay. All 12 inherited parent streams are byte-identical |
| Alternate neutral assembly | An authored empty exploded-view manager moves component IDs from `17,18` to `18,19`. Alternate names and opposite order survive independently decoded as `Gauge alignment` and `Fixture access`. The new 1,795-byte map-39 store is the sole stream delta against that assembly's own baseline |
| Owner checks | Actual `AssemblyActive` config `0`, binary contexts `18,17` in the native-tested profile, plane rows `14,13,12`, pooled locator and title identity, shared null properties, and both independently joined header clocks |
| Runtime and refusal | Two fresh processes, 16 repeatable complete builds, zero audited external accesses and 13 scoped refusals |

The refusal cases cover missing states, inconsistent default, foreign names, numeric flags, duplicate names or vectors, a stale manager locator or configuration alias, authored datum chronology, flag-eight context, child appearance store, detached Header owner and a different mate rotation lock. The node layouts are scoped to this outgoing stream; they do not admit additional ordinary CMgr or Config/Resolved owners. Formatting and repository steering passed for all nine changed production files. The donor scan passed on 82 assembly and visual codec files.

```sh
report_dir=$(mktemp -d /tmp/KitSdkConcentricVisual.XXXXXXXX)
python3.14 -I -B re/tooling/sw2026/para/concentric/VerifySdkVisualStore.py \
  verify "$report_dir/Result.json"
```

The [guarded result](../measurements/2026/SdkConcentricVisualStore01.json) has SHA-256 `e811c03a9bdbdfdd650f91228d7c6a77cc65ff82e640b66ea0c442508d606c3f`. The 5,041-file SDK manifest is `fd35c4403cb83659cd751b77f4530646f481ace21187ce06e01892c966b7d45e`, based on `97656af81560dc37f3fd10a176afa39a69e05b02`. The verifier SHA-256 is `e466895eccc3f60aa678f72826c14582667807d8601495e7df3e2c0e00e788ba`.

## Original source boundary

The later [singleton proof](ConcentricDefaultDisplay2026.md) verifies
the internal default state with the actual disclosed D01 design
projection. It preserves every measured three-state output.

The synchronized disclosed D01 has historical parent contexts using flag 8, a populated manager locator, real plane creation events and its own populated child display appearances. The generated-child absence experiment covers initial generated binary visibility only. Actual source appearance and chronology must retain their own authority before endpoint-preserving source projection can request this writer. Source native payloads and field operands remain outside the generation input. The exact prior evidence applies to the measured artifact. The alternate allocation is host evidence and the held-out files remain sealed. [Source owners and time authority](ConcentricVisualStateStore2026.md) · [Child appearance boundary](ConcentricChildAppearance2026.md) · [Whole-source prerequisite register](ConcentricSealedAdmission2026.md)
