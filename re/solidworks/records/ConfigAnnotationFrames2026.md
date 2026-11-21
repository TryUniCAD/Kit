# Ordinary SOLIDWORKS configuration annotation defaults and tolerance frames

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-ANNOTATION-FRAMES` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-annotation-frames` |
| Preparation base | Accepted main `72207ec5684d89bf98023427ce4f49eac3a5d122` |
| Dependency | Shared configuration field actions, character and line width formats, and the part and ModelHeader map link |
| Exit | Both bounded source replays and guarded wire contrasts, followed by current-revision review and applicable CI |

## Physical owners

The existing 2026 SP05.2 reader trace binds the defaults to `moDetailDefs_c.f1f18` and the tolerance data helper to `moDetailDefs_c.f9a0`. Both are within the ordinary `moModel_c.fae0` detail section. The detailing calls share the physical `moPart_c` owner. The part descriptor, part object and prior external self reference occupy slots `1`, `2` and `3`. The helper frames are embedded rows under `f9a0.f08`, with no runtime class tag of their own. The aggregate trace records each inline call, both streams' digests, and the archive cursor and map at entry and return. [Pinned trace](../measurements/2026/ConfigAnnotationSource01.json) · [2026 serializer evidence](https://github.com/TryUniCAD/Kit/blob/e4093f012e61a6a4e2aafb029b376dcb23c50e9b/re/solidworks/records/AnnotationArchive2026.md#composition-and-field-ownership)

| Tracked source | Defaults interval | Tolerance helper interval | Tolerance frames | Observed incoming and outgoing counter |
| --- | --- | --- | --- | --- |
| L1 blind boss | `[9185,11141)` | `[17950,18338)` | `[17954,18006)` and `[18006,18058)` | `69 → 69` |
| Concave import | `[7634,9590)` | `[16531,16943)` | `[16535,16587)` and `[16587,16639)` | `54 → 54` |

The defaults contain ten inline owners, including nine concrete suffixes using the shared base and one base-only direct member. Each uses two line widths and a character format at their actual positions. The stored `f44` selector is a signed 16-bit word, with `-1` indicating absence when condition `0x40000000` is set. A non-`-1` selector in that conditional branch reaches the unqualified `f48` layer object and refuses before consuming its tag. [Annotation default layout](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/BaseAnnotationFields.py)

The tolerance helper begins with a signed 32-bit frame count. Each frame holds six counted `su_CStringArray` values, two nullable tolerance references, unsigned 16-bit datum selector `f148`, and signed 32-bit indicator count `n2b8`. A nonzero datum selector reaches three unqualified datum owners. A positive indicator count reaches an unqualified indicator layout. The bounded reader also refuses negative counts, a foreign part root, an unrecognized inline owner and populated tolerance references, including otherwise valid objects already in the inherited map.

## Verification and boundary

The isolated reader consumes the two bounded owner intervals after the normal part/ModelHeader read. It seeds the actual three part-start entries. The pinned full-configuration trace supplies the later physical counters because these two groups allocate no slots. The guarded proof emits each interval again through the shared typed field writer and compares every byte, including each base and frame sub-interval. The two original documents provide 28 exact body comparisons. Independently authored wire contrasts verify a nonempty mixed ANSI/Unicode frame string array and one or zero helper rows. Additional contrasts check both sides of the signed layer selector condition, truncation, trailing data, wrong version, foreign owners and unsupported populated branches. [Guarded process receipt](../measurements/2026/ConfigAnnotationArchive01.json) · [Queue process coverage](../../../tests/Convert/Solidworks/Configuration/Annotations/CfgAnnTests.py)

Run the process evidence from the repository root.

```sh
python -I -B re/tooling/sw2026/CheckCfgAnn.py ladder
python -I -B re/tooling/sw2026/CheckCfgAnn.py concave
python -I -B re/tooling/sw2026/CheckCfgAnn.py wire
```

Refresh the physical trace with `python -I -B re/tooling/sw2026/TraceCfgAnn.py` when the pinned aggregate revision is present in the Git object store. The scoped replay requires the tracked sources and the pinned trace receipt. The process rejects file, process and network use after ingest and module loading. Native launches were zero.

The next configuration dependency is the remaining detailing parent and annotation helper groups, including note and finish ownership. The two L1 annotation-view objects use a separate tagged list and require their own repeated-reference guard. Complete Config-0 and #183 public literal-property admission still require the full model and detail layouts and exact section consumption. [Physical delivery plan](https://github.com/TryUniCAD/Kit/blob/e4093f012e61a6a4e2aafb029b376dcb23c50e9b/re/solidworks/records/ConfigPhysicalDelivery2026.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
