# Allocation counts in the ordinary edge fillet rollback

Task `B04-SW2026-EDGE-FILLET-SOURCES` in PR #121. The typed
transaction work starts at `8ea2fa45b285499f1f50c61f04b29c7f0649ebf4` and
uses SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` with the current
`SCH_3701250_37102_13006` partition grammar.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
[Writer model](../../Playbook/WriterModel.md)

## Confirmed allocation count rule

For a backward delta, count each physical removal in the active state
toward `PMARK.n_new_nodes`. Count each physical restoration in the earlier
state toward `PMARK.n_del_nodes`. Add the hidden pointer-value allocations
owned by those same nodes in the corresponding state. They remain
allocated when the pointer array's one member is null. Neither a retained
previous-copy row nor a declared but unallocated field adds a node to these
counts.

The exact kernel SHA-256 is
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`.
The allocation path for a positive-count pointer-value field is
`0x180a87204–0x180a8721b`, and `0x1814391d6` marks this class
nontransmittable. The rollback count selection at
`0x1819e9eeb–0x1819e9f06` follows the actual delta direction.
[Pointer allocation and transmission](GeneratedRectanglePartition2026.md#native-ownership-rules)
[Directional count selection](ThroughAllMultiStockHistory2026.md#field-ledger)

The [guarded receipt](../measurements/2026/EdgeFilletRollbackCounts01.json)
binds the typed removed and restored attributes to their declared field
kinds through the current and prior graphs.

| Disclosed saved fillet state | Physical removals + hidden | `n_new_nodes` | Physical restores + hidden | `n_del_nodes` |
| --- | ---: | ---: | ---: | ---: |
| Axial original | 61 + 5 | 66 | 26 + 1 | 27 |
| Axial edited | 60 + 4 | 64 | 26 + 1 | 27 |
| Transverse original | 64 + 5 | 69 | 29 + 1 | 30 |
| Transverse edited | 63 + 4 | 67 | 29 + 1 | 30 |
| Generated axial derivative saved before the native shutdown failure | 60 + 4 | 64 | 26 + 1 | 27 |

Every selected removal group owns two hidden fields on its new
`FACE_ID_2001` and one each on `BODY_RECIPE_2001` and
`BODY_IN_LIGHTWEIGHT_PERM`. The two original saves also remove the one
pointer field on `FACE_AUTOMATION_2_2001`. Their edited states omit that
attribute from this transaction. The restored allocation is the hidden
field on the prior `BODY_RECIPE_2001` in all five states.

The preceding stock rollback has 142 physical removals and 16 hidden nodes
in all five files. The six stock face identities account for 12. The
body recipe, time stamp, atom identity and last modifier account for four.
The lightweight allocation belongs to the observed fillet transition.
This explains the difference from the earlier ordinary prism study's
17 additional nodes.

## Model-owned counting

`CountRollNodes` accepts the actual rows for one transition arm, that
state's graph and the pointer allocations explicitly supplied by the
constructor. It checks actual member identity, declared pointer field kind,
the absent wire reference and unique slot positions. The attached cylinder
tracks each generated pointer allocation by its attribute and field. Its
existing selected PMARK uses the same rule.
[Shared counter](../../../src/convert/adapters/solidworks/Archive/Partition/History/CountRollNodes.py)
[Cylinder mark constructor](../../../src/convert/adapters/solidworks/Archive/Partition/AttachedCylinder/MakeCylMarks.py)

Seven input-guarded workers consume the five hash-pinned saves or independently
generate two different cylindrical partitions from authored inputs. Each
selected cylinder mark has 53 physical removals and 11 hidden allocations,
and both typed history readers agree. Both model variants refuse detached,
duplicate, foreign, and wrongly typed allocation claims. The established
concentric preparation proof also re-emits both previously accepted whole
parent-child pairs byte-for-byte. No source bytes enter the partition
constructor and these comparisons add no native or held-out credit.
[Existing concentric verification](SdkConcentricChildModel2026.md#guarded-comparisons)

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/AuditFilletNodeCounts.py \
  --capture /path/to/disclosed/EdgeFilletSource03/Capture \
  --generated-axial /path/to/disclosed/EdgeFilletAxialEdited.SLDPRT
```

## Open copy-count boundary

The count of changed typed rows does not give the native processed copy
count. The axial delta has 55 physically different previous rows and a
processed count of 40. The transverse original and edit have 57 and 53
different rows and the same processed count of 37. Their staging counts
are 79 and 81, with 76 and 78 previous-copy rows respectively. Trace the
temporary processed-count substitution at `0x1819f0d92–0x1819f0dc0` and
the per-kind staging filter at `0x1819ea69d–0x1819ea6b1` to identify those
allocations independently of the physical diff. The internal pointer
qualifier limit and the operation's topology mutation order remain open.
This work emits no fillet archive and makes no claim about the earlier
candidate lifetime failures.
[Retained transaction](EdgeFilletRollback2026.md)
[Native candidate outcome](EdgeFilletModelCold2026.md#first-native-candidate-bracket)
