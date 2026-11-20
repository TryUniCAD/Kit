# Saved two-stock active geometry

This internal read step advances `B04-SW2026-EXTRUDE-THROUGHALL` under PR #121. It groups the selected-scope save’s decoded geometry using the two actual live atom identities. The disclosed selected input is SHA-256 `748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3`. The native bracket and upstream edit are recorded separately. [Saved lineage](ThroughAllMultiStockArchive2026.md#bounded-typed-lineage) · [Native measurements](../measurements/2026/ThroughAllMultiStockScopeObserved01.json)

## Active partition and body identities

`ReadStockCache` starts from the same archive for the selected Config-0 lineage and active kernel data. It requires complete partition and delta wrapper coverage in `Contents/Config-0-Partition`, with schema `SCH_3701250_37102_13006`. From the active payload it checks the complete linked WORLD graph, the reciprocal two-body chain, registered attribute definitions and each body’s actual owner list. The kernel attributes bind `ATOM_ID_2001[1]` to the surviving atom, `BODY_MATCH[0]` to its cache tags and `LAST_BODY_MODIFYING_FEATURE_ID[1]` to its producer. The observed pointer mirror slots are zero. The implicit body labels are read from their actual kernel owner and checked against the linked producer after the numeric join. [Internal entry](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cache/ReadStockCache.py)

| Kernel BODY index | Live atom | BODY_MATCH | Actual feature | Decoded faces |
| ---: | ---: | ---: | --- | ---: |
| 2 | 102 | 3597 | `MovingStock`, ID 40 | 6 |
| 6 | 103 | 3121 | `ThroughFeature`, ID 47 | 8 |

The consumed atom 101 also carries BODY_MATCH 3121. The actual active body identity and producer therefore establish the join. The typed shell sides give the same FACE inventory for each solid. Decoded face and surface IDs use the encoded short, which is the normalized native transmit index plus one in this bounded profile. The read requires all native FACE identities, every decoded face and its carrier, and a unique full face-set match for each decoded solid region. It rejects detached or alternate shells and regions. [Typed boundary](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cache/ReadCacheFaces.py) · [Decoded grouping](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cache/MapStockBrep.py)

The result keeps both actual native producer objects for subsequent timeline binding. BrepBody and prospective design-body IDs follow each live atom, with the untouched producer followed by the cut result. The receipt verifies that replacing only the public-decoder body aggregate restores the original decoded geometry. In-memory reversal of the reciprocal WORLD body chain yields the same grouped B-rep and body order.

## Separate history boundary

The existing strict delta decoder reaches PARTITION index 377 and current PMARK index 378, logical mark 21 with delta key 3. At decompressed delta payload offset 144, the rollback parser expects framing words `0001 0001` and receives `0062 ff00`. The scope of the active geometry proof is distinct from decoding that rollback record. The existing single-body attribute registry checker also refuses the two actual `BODY_IN_LIGHTWEIGHT_PERM` heads, `(attribute 4, BODY 2)` and `(attribute 45, BODY 6)`. The active grouping uses the registered definition inventory and verified per-owner chains. [Delta decoder](../../../src/convert/adapters/solidworks/Archive/Partition/ReadRollbackMut.py#L13) · [Exact refusal in receipt](../measurements/2026/ThroughAllMultiStockCache01.json)

## Guarded host evidence

The receipt binds source baseline `5b51280a4d9ddf03a35445650a8c5c4077e523a3` and the ten new implementation file hashes. Its SHA-256 is `c62c3bd6604a3916729ed474eade455906d790955ed86135e092a2b9a78f82f0`. Nine fresh stdin-only Python processes reported zero guarded external access attempts after dependency loading. Besides the disclosed original and the WORLD-order contrast, the worker refuses the consumed atom, a crossed producer, a detached WORLD body, a detached native face, a crossed surface carrier and an alternate pointer mirror. The independently disclosed unrestricted save is SHA-256 `f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22`. It confirms the selected-scope entrance refuses the other mode. Scoped steering and Mypy passed all ten Python modules. [Receipt](../measurements/2026/ThroughAllMultiStockCache01.json)

```sh
disclosed='/Users/odin/Documents/UniCAD/Oracle121Takeover'
python3.14 -I -B re/tooling/sw2026/throughsource/ProveStockCache.py \
  --selected "$disclosed/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT" \
  --unrestricted "$disclosed/ThroughAllBodies02/DisclosedNative/ThroughMultiStock.SLDPRT"
```

Public admission still requires a complete typed native timeline mapping of the two independent blind producers, all three actual profiles and the selected through-all cut, with its design-body and topology links, supported default owners and controls. The active result is available to that work through the internal entry. It carries zero held-out, production and corpus credit. [Current public body binding](../../../src/convert/adapters/solidworks/Core/Adapter.py#L404)
