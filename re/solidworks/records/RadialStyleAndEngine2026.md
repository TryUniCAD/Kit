# Ordinary local radial style and engine construction

Status: hash-bound native construction rules and an unqualified research synthesis candidate. No driving-dimension, appearance, extrusion or held-out acceptance follows from static analysis.

The target is SOLIDWORKS 2026 SP05.2, executable `34.5.2.0604`. The [style evidence](RadialStyleConstruction2026.json), [pattern evidence](RadialPatternSemantics2026.json), [engine evidence](RadialEngineConstruction2026.json) and [field delta ledger](RadialEngineFieldRules2026.json) retain original module identities, complete chained function boundaries, actual vtable cells, imports and instruction-window hashes. Root independently checked frozen authored manifests and original-image hashes for 93/38/82 function groups, 54/10/52 cells and 4/15/14 instruction windows respectively. Every read span was bounded by raw section size. No vendor code, listing, saved field program or native payload is included.

## Constructor and caller context

The position-taking base constructor is `[0x4c86ede0,0x4c86f54c)`, followed by radial constructor `[0x4c8bfc10,0x4c8bfe5a)`. Common initialization still uses the common display vtable: its dynamic value array has one zero element. The later radial vtable selects subtype, text kind, position update and engine. A nonnull style model is distinct from dimension feature ownership. The constructor's common engine returns early with a null feature owner; a separately modeled owned update refreshes its array element from the actual parameter.

The position-taking base applies `(fb64 & 0xfffffef7) | 0x80a05`; the feature constructor uses `0x80205`. Both agree from native seed `0x1870`, since bit `0x800` was already set. Copy explicit dimension-root `fd8` bit `0x100000` and retain the later `0x30000/0x44000` operations. Embedded text receives the authored point at `f6a0.f38`, with ordinary radius kind `0x14` or diameter kind `0x11`. Selected leader `ff80` remains an explicit signed32 input; its constructor supplies no neutral default.

## Explicit model style

Let `D` be effective detail root `f13b0`. Radius selects `S=D.f3f8`; diameter selects `S=D.f960`, under ordinary nondrawing/noncallout guards. Each operation preserves unrelated bits.

| Wire field | Derived rule |
| --- | --- |
| `f870/f874` | `D.f6c`, admitted to u16 |
| `fb68/fb6c/f8ec` | `S.fc/S.f10/S.f84`, each admitted to u16 |
| `f8a4 & 0x40` | Clear if `f8f4==1` or `f8f4==2 and D.f74!=0`; otherwise assign from `D.f60==0` |
| `f8a4 & 0x10` | Assign from `bool(D.fd8 & 2)` |
| `ffd8 & 4` | Radius `(S.f100 & 4)==0`; diameter `(S.f104 & 2)==0` |
| `ff00/ff10` | `D.fc0` and `int(bool(S.fe0 & 0x10000))` |
| `fb64 & 0x1000/0x2000` | Assign from `S.f78!=0` and `S.f9c!=0` |
| `fe40` | `S.f08`; owned update reselects the owning model's subtype |
| Tolerance | Initially null private tolerance remains null under `S.f44==0` and the no-sharing/no-equation guards |
| `f30c/f320` | Typed copies of `S.fd0.f10/S.fd8.f10`, independently of lookup success |
| `f308/f31c` | Change only if the corresponding ordered catalog lookup succeeds |

Initial precision changes skip their observer body while runtime initialization mask `b5c & 0x100000` is set. Later owned changes require separate evidence.

The normal session catalog bridge can select the primary thread's active document or environment manager. The style-model argument does not itself select that catalog. Lookup finds the first nonnull ordered row matching the query-length UTF-16 prefix through native `_wcsnicmp`; Python case folding is not established as equivalent. Loading clears the current list before appending rows. The generated Definition explicitly has an empty catalog, so the candidate models no successful lookup and preserves constructor indices. Those indices establish no named pattern, builtin row or appearance acceptance. No installed `.lin` library is read.

The pattern proof separately admits an explicit `CONTINUOUS` row with one explicitly authored finite positive segment for the inspected consumers. It supplies no segment magnitude or physical-unit conversion. Signed ordered rendering, repeat-count domains, count-zero discrepancies and optional center-snap predicates remain recorded separately; the first radial candidate rejects the center-text style branch.

## Position and engine

In general preserve native order: `C0=Apply(center,Inverse(T))`, `P1=Apply(text,T)`, `C2=Apply(C0,T)`, `d=(P1.x-C2.x,P1.y-C2.y,0)`, where `T` is actual profile `pd_ff0`. Do not cancel transforms by assumption. The first candidate admits only an explicit canonical front frame and on-plane text point.

| Wire field | Rule under the stated guards |
| --- | --- |
| `f880` | Normalize `d` when its largest absolute component is at least `1e-8`; otherwise native positive X. Check finite squared length and separate `1e-17` unit-vector threshold |
| `f8a8/f8b0` | For `V>1e-8`, with `R=V` for radius or `V/2` for diameter, compute `sqrt(dot(d,d))*(1/R)` and `sqrt(dot(d,d))-R`; otherwise preserve constructor seeds |
| `fad0` | Norm of actual reference difference `C0-zero` when the native component predicate is nonnull, otherwise parameter `V`; not universally the radius |
| `f958/f988` | Apply `C0` through ordered native composition of `T` and inverse fresh identity delta |
| `f950` | Actual private parameter `V` |
| `f5b0` | One model-generated binary64 `V` after an explicitly modeled owned common update |
| `f3e0 & 0x200` | Clear through broken-area setter with empty attachments |
| `f8a4 & 0x8000` | Clear under actual local/valid/active-owner dangling predicates |
| Radial `f1010/f1028` | Positive-zero witnesses after full-circle endpoint query returns false |
| `ffd8` | Native seed `0x80086`; explicit style bit four; assign bit `0x10` from current mode; late ORs `0x100000/0x200000` |
| `f7f8/fb60` | Native prefix `R` or `<MOD-DIAM>`, then actual use-instance bit `0x200` |

Six radial scalar caches retain documented constructor zeros. Optional transform/callout/mirror/Hole Wizard/auxiliary-list pointers are absent under their constructor guards; string counts follow their collections. Shared fields inherit common constructor rules before any distance/angular subtype suffix. The [field plan](CircleDimensionFieldPlan2026.json) retains earlier distinctions and unresolved final claims; the newer ledger refines the local style/engine boundary without declaring final saved acceptance.

## Solve and acceptance

Entity `f30=5/f34=1`, sketch `f12c=1/f128=1` and stamp `1+permanence_operations` are native pre-solve construction states. The [free-circle measurements](../measurements/2026/CircleSketchInspection01.json) apply to that earlier graph only. Added value/display dimensions need their own native load/rebuild/edit/save/fresh-reopen checks; no captured fixed-center status replaces a solver answer.

Actual ordinary-profile admission reaches the pending node's `f0c & 1` before cache/status fallbacks, and `f3dc==0` selects its ordinary engine. This does not prove engine success, numerical solve, final stamp/status, contour regeneration or callback preservation.

The private parameter keeps independent constructor ID `-1`. Dimension `f50` uses the shared header allocator at naming. The fresh empty namespace supplies `D1`; actual circle add/remove-ref overrides are no-ops, retaining dimension refcount zero. Entity constraint count instead follows the added arc reference. All collection lengths, compact/extended indices and map topology come from the generated graph.
