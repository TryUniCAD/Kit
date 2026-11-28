# Constrained rectangle stock for a cold SOLIDWORKS shell

Task `B04-SW2026-OPEN-SHELL/stock-relations`, owned by `/root/release_path` for PR #121. Base `bd3ab078476c403e5615fc1f0eca6b29dd770747`. This stage preserves the first stock sketch's authored axis and endpoint constraints through independent model construction and strict SDK readback. It follows the existing [fresh and saved shell inspection](ColdOpenShellReader2026.md). Native candidate acceptance, complete saved-source transfer and public writing remain open.

## Source evidence and exact owners

The [pre-writer source lock](https://github.com/TryUniCAD/Kit/blob/84d925a36c79c2b3124aba3ac06830c95297bca1/re/solidworks/measurements/2026/OpenShellSourceLock01.json) is `d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b`. The lock records eleven completed native process lifetimes and was committed at 07:23:00 PST on November 22, 2026. The first model-only constructor commit `52646d90ab8914e2f8548d5635d97ddd15b8dea3` followed at 07:53:47 PST on a separate branch. Two independent sources and their observations remain under the oracle owner's custody. The disclosed pair is the original 2.8 mm wall and its 3.53 mm edit on the same 53 × 41 × 28 mm stock. Both retain one inward shell, the actual top-cap pick and two independent `D1` owners.

The original and edited source files both contain four typed unary rows in `sgSketch.dims.log_g1`. Each `sgLineHandle` resolves to a distinct active segment, with native horizontal code 4 or vertical code 5. The four remaining coincidence relations are the actual shared point identities. The source rectangle has two lines directed opposite to the closed-loop traversal. Its corners therefore include start/start and end/end as well as end/start references. The existing free cold shell lacked those eight editable relations.

The [shell projector](../../../src/convert/adapters/solidworks/Core/Preparation/Shells/ReadShellRect.py) requires four original axis relations and an exact one-to-one correspondence between authored endpoint pairs and real adjacent corners. It derives a canonical forward contour for the common rectangle composer only after checking original handles. Extra, suppressed, non-driving or misattached relations refuse. The [shell stock constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Shells/MakeShellStock.py) reuses `MakeAxisOnlyMut` for the native relation owners and shared point/ring construction for the corners. Neither the previous free profile nor the default chamfer scope changes.

Strict readback uses the actual typed axis records and reconstructs the four shared endpoint relations. Both inspection modes keep those rows, the two real drive parameters and earlier cap selection. The full mode also keeps the closed one-solid shape with eleven faces, twenty-four edges and sixteen vertices. The private compiler reapplies the exact complete readback check after repeating a cold archive.

## Guarded source boundary

The [process probe](../../tooling/sw2026/shell_source/VerifyShellRelations.py) reads the two exact disclosed source hashes outside the compiler. Each worker projects their semantic contour, constraints, drivers and cap into a new neutral model. This projection represents the scoped authored geometry. The original saved documents continue to refuse the cold compiler because their full physical saved envelopes require separate ownership rules. An independently authored translated rectangle exercises the same constraints at different dimensions and bounds.

| Candidate | Bytes | SHA-256 |
| --- | ---: | --- |
| Original-source neutral projection | 8,977 | `1bf01c7f4e485c70e6cce2f962de65abd50956c66f520e8249eda40e413db057` |
| Wall-edited source neutral projection | 8,975 | `93afd11653b73c04e925b65c06bf92b928140eeffd2e8e8accf31529eddb3886` |
| Independent translated neutral rectangle | 9,013 | `aec29066c47e9f6585356d41fb30a2c568e7015d3103a1ee4a1114f1262559f7` |

The three fresh guarded workers compare all 30 emitted logical streams, the actual relations, native owner roles and independently calculated geometry. Twelve complete strict readback compilations reproduce the candidate bytes, including inspection JSON validation. They refuse an incomplete relation set, wrong axis, wrong endpoint owner, duplicate pair and non-driving join. A typed counterexample swaps the independently valid native axis codes and is rejected in both strict modes for disagreement with the selected lines. Six attempts through direct and registry public writers leave their sinks untouched. No CAD process runs during construction.

The four established cold models, the two native-written warm states and the native stock control also pass their existing guarded procedures. The prior free calibration remains byte-identical. The [receipt](../measurements/2026/SdkColdShellRelations01.json) binds the scoped implementation and current three outputs. The licensed oracle remains responsible for actual native open, rebuild, edit and fresh reopen. Held-out credit requires both pre-writer locks to pass their independent comparisons. These new candidate files add no corpus conversion credit.

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/VerifyShellRelations.py \
  --disclosure /absolute/path/OpenShellSource02/Disclosure \
  --output /tmp/KitShellRelationProof
```

Use a fresh output directory outside Kit. The candidate's encoded Windows locator is part of the receipt. Native tests can place these exact candidates at those locators and compare the actual four axis usages and four shared corners before and after the original wall edit, alongside the existing healthy controls and geometry checks. The old free calibration packet remains independent.
