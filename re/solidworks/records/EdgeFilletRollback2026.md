# SOLIDWORKS 2026 edge fillet rollback ownership

The strict delete-only history reader refuses the four disclosed single-edge fillet originals and edited saves. The [bounded physical audit](../../tooling/sw2026/edge_fillet_source/AuditFilletHistory.py) consumes all four delta payloads and follows their actual predecessor states. It also passes the same immutable ordinary revolve control, whose selected rollback deletes its body. This is an offline result for SOLIDWORKS 2026 SP05.2 x64 build `34.5.2.0604`, on the previously measured `SCH_3701250_37102_13006` kernel grammar. [Disclosed archive evidence](EdgeFilletArchive2026.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Reverse engineering playbook](../../Playbook/README.md) · [Corpus correlation](../../Playbook/CorpusCorrelation.md)

## First physical difference

The current `ReadRollbackMut` expects the empty restored-row terminator immediately after the selected PMARK. All four fillet saves instead begin the restored sequence with a real class 98 `UNICODE_VALUES` record. It occupies record-body bytes [51, 90), at [144, 183) in the decompressed delta payload. The wire record consumes a big-endian u16 kind, one first-use descriptor byte, a big-endian u32 element count, a short transmit index and fifteen u16 words. It restores field zero of `SWIMPLICITBODYNAME_ID_U` on the retained body. The decoded value is `FilletStockBoss`. The active value is `ConstantEdgeFillet`. The restored string is slot 210 in the originals and 209 in the edited saves. The slots belong to those samples. [Shared Unicode class fields](../../../src/convert/adapters/solidworks/Archive/Partition/Fields/AttributeShapes.py) · [Existing rollback reader](../../../src/convert/adapters/solidworks/Archive/Partition/ReadRollbackMut.py)

The audit reuses the full-row reader from the [previous exact-build history study](ThroughAllMultiStockHistory2026.md), bound to `pskernel.dll` SHA-256 `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`. That study traced the restored rows, removal pairs, copy staging and terminators at `0x1819ea192`, `0x1819ea4e5`, `0x1819ea55a` and `0x1819ea811`. The qualified pointer encoding follows `0x1819ee254–0x1819ee26c`. These facts are confirmed for the reached framing. The audit consumes each row through its existing current class schema, validates null and repeated pointer qualifiers, checks ownership in the actual preceding state, and reaches the full payload terminator. The qualifier's internal allocation limit and the native producer's filtered copy inventory still require construction evidence. [Pinned physical reader](../../tooling/sw2026/throughsource/ReadTwoStockHistory.py)

| Disclosed save | PMARK new / deleted / processed copy counts | Physical restored / removed / previous copies | Copy staging |
| --- | ---: | ---: | ---: |
| Axial original | 66 / 27 / 40 | 26 / 61 / 76 | 79 |
| Axial edited | 64 / 27 / 40 | 26 / 60 / 76 | 79 |
| Transverse original | 69 / 30 / 37 | 29 / 64 / 78 | 81 |
| Transverse edited | 67 / 30 / 37 | 29 / 63 / 78 | 81 |

The actual Config-0 activation owner and stock and fillet `f3d0` records are present in the linked map. They select 3, 13, 17 in each original and 3, 25, 29 in each edit. Chronological traversal uses the reciprocal PMARK links. It reaches the earlier stock, an activated body-free WORLD, and the initial inactive WORLD. The physical order stores the selected mark first, followed by the initial, activation and stock marks. The selected rollback copies the previous BODY and WORLD under their existing slots. It changes the modifier from fillet 34 to stock 32 while keeping atom 101 and its measured matching body tag. The next rollback deletes that body. [Typed mark schema](../../../src/convert/adapters/solidworks/Archive/Partition/Fields/WorldShapes.py) · [Exact numeric receipt](../measurements/2026/EdgeFilletRollbackRead01.json)

## Physical stock and selected edge

The restored stock passes the complete shared rectangular body topology check. Its eight vertices match the independently authored stock dimensions. The actual fin pair finds one straight edge with the two measured native selection endpoints. The four ordered `f848` surface representations join to the previous planar faces through their actual `FACE_ID_2001` class code, creator ID, header creation word and ordinal. This uses the existing planar ID rule from the prism study. [Native face identity evidence](PopulatedPrismPartition2026.md#topology-and-ownership) · [Body and support audit](../../tooling/sw2026/edge_fillet_source/FilletHistoryBody.py)

| Selected edge | First two records and actual incident planes | Last two records and endpoint-only planes |
| --- | --- | --- |
| Axial | side 2, side 1 | end 1, end 0 |
| Transverse | end 1, side 3 | side 2, side 4 |

Both adjacent planes contain the complete edge. Each remaining plane contains exactly one endpoint. In these four files the endpoint-only records list the higher coordinate first on the selected world axis. The samples establish the measured incidence and order. General handed ordering, edge stamp computation and generated attribution require further evidence.

## Scope and verification

The existing `ReadXmtHistory` combines a single previous WORLD record with a selected-body deletion check. Relaxing its first sentinel would still leave the retained BODY and restored attribute ownership unverified. A production reader for this branch needs a separate result that retains typed restores, removes and previous copies, then validates the complete historical owner graph. The existing strict callers use the narrower delete-only result. The audit's control passes that result and identifies prior mark 3. The four fillet files still reach the expected strict framing refusal.

Five fresh local workers perform the guarded reads. Each fillet worker also rejects a crossed removal class, contradictory repeated pointer qualifier and insufficient previous-copy capacity in separately modified typed graphs. All five workers record zero guarded external access. The receipt SHA-256 is `a8b954ac2eab2d5064055282cf1f029bec4d0a2ba83c4b09e1023d646f06b849`. Private originals remain sealed and this observation establishes no writer or public acceptance. [Retained body gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/History/FilletRollbackRetainsBody.md)

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/AuditFilletHistory.py \
  --capture /absolute/path/to/disclosed/EdgeFilletSource03/Capture \
  --control /absolute/path/to/disclosed/EdgeFilletSource03/Packet/Control.SLDPRT \
  --report /absolute/new/EdgeFilletRollbackRead01.json
```
