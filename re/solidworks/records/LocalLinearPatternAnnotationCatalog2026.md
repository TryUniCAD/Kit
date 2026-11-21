# Model-owned annotation catalog for the angular datum

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. A research-only Config-0 composer creates separate unbound annotation views from their authored order, names and signed model-axis frames. The current and shown view states are explicit inputs. A display membership resolves to the actual output view ID. The ordinary camera catalog is independent. [Exact receipt and tool hashes](../measurements/2026/LocalLinearPatternAnnotationCatalog01.json) · [Previously proved angular view ownership](LocalLinearPatternAngularDatumOwners2026.md)

| Owner | Provenance and rule |
| --- | --- |
| `moPart_c.fa48` and `feb0` | `addAnnotationView` appends the actual new view to the list at `+0xa48`. The ordinary fresh frontier is 199. The native annotation allocations at `0x4c013c86` and `0x4c7e9a72` increment `+0xeb0` before passing its assigned ID to the constructor. The composer assigns one unique ID for each authored view in actual order. The highest allocated value becomes `feb0`. |
| `moAnnotationView_c.f360` and `f368` | Uses the generated ID and the independently authored proper origin-frame rotation. The common view initializer supplies the base state. The unbound initializer `[0x4c7e8470,0x4c7e8763)` seeds the concrete annotation members. The composed frame uses the ordinary rigid transform representation. An actual identity rotation needs no matrix. The unbound scope has no component, plane, parent or folded-geometry owner. |
| `moPart_c.feb4` and `nec8/fec0` | `getCurrentViewId` obtains `+0xeb4`. `showAnnotationView` uses the separate sorted unsigned ID set at `+0xec0`. The ordinary Config store at `0x4c234b93–0x4c234bf2` writes frontier, current ID, shown count and IDs independently. Explicit default annotation membership is ID 199. An absent current annotation maps to that ID. |
| `moDisplayAngularDim_c.f2b0` | The membership writer resolves the authored display's name in the actual generated model-owned list. The common display getter resolves the stored ID through the model. It treats 199 as unassigned. A same-name camera and its own transform stay in `f9f8`. |

The proven domain is a previously empty current-release part catalog with up to three independently authored nontranslated cardinal views. The tool refuses malformed bases, ambiguous names or shown membership and missing activity references before mutation. Referenced annotation views, arbitrary rotations and automatic source camera selection require separate construction rules.

The four angled disclosures and two independent principal-pattern controls preserve the actual ID order and state. The model-derived transforms and concrete annotation members match their 13 rows under numeric equality, including the matrix-free identity Front view. This source comparison uses the already pinned complete Config-0 replay. The normal shared constructor creates a new empty `fa48` and seeds 199/199. The research composer uses these existing rules and supplies only the requested additions. [Typed generator](../../tooling/sw2026/linear_pattern/MakePatternAnnotationCatalog.py) · [Host and isolated process comparison](../../tooling/sw2026/linear_pattern/ProvePatternAnnotationCatalog.py)

| Guarded neutral model | Authored view order | `*Back` join | Current view | Shown IDs | Config-0 bytes before and after | Map growth |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `FirstAnnotationOrder` | Back, Top | 200 | 199 | 199 | 22274 → 22814 | 3 |
| `SecondAnnotationOrder` | Top, Front, Back | 202 | 200 | 199, 202 | 22276 → 23008 | 4 |

Four fresh processes consume neutral stdin with zero runtime file reads. Each result replays the generated Config bytes and linked map. Resetting only the annotation list and declared view state in a separate readback graph reproduces that model's ordinary Config bytes. Five malformed requests per model leave their ordinary bytes exact and refuse at the corresponding guard. The two new lists carry different positive IDs for the same semantic `*Back` target. The output is Config-0 in memory. Completing the angular feature still requires the arc display and complete neutral feature graph. The native-process and protected-input counts are both zero.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternAnnotationCatalog.py \
  --binaries /absolute/licensed/module/directory \
  --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/AnnotationCatalog.json"
```
