# Strict reads of generated principal linear patterns

Task `B04-SW2026-LOCAL-LINEAR-PATTERN/cold-read` · owner `format_proofs` · delivery PR #121. The proof starts at `bd3ab078476c403e5615fc1f0eca6b29dd770747`. The two origin-stock and two placed-stock inputs are the exact generated version-19000 Right-forward and Top-reversed controls. Their whole-file hashes, typed dimensions and independent geometric expectations are bound by the existing receipts. [Origin-stock receipt](../measurements/2026/LocalPrincipalPatternContainer01.json) · [Placed-stock receipt](../measurements/2026/LocalPlacedPrincipalPattern01.json)

On the prior reader, both origin files failed full strict open with “SLDPRT contains no readable Parasolid payload”. Design-only reads fell back to the untyped pattern step. The old cold path required a hinge and a Back annotation catalogue, even though the actual principal direction, stock and final atom were already representable in the linked archive. [Direction evidence](LocalPrincipalPatternDirection2026.md) · [Driver evidence](LocalPrincipalPatternDrivers2026.md)

## Reader scope

- The cold principal lane requires the existing ordinary 22-root plate/seed/pattern history, no resolved body-map trailer and the actual linked live result atom. The selected line must agree with its existing canonical Right or Top plane, signed role, both header creation logs and measured display extents. It applies the existing contained raised geometry to the actual placed stock.
- The part's ordered annotation catalogue, allocated IDs and view frames must match the witnessed signed mode. D1 joins its own Front annotation. D3 joins the actual Top or Left annotation. D2 and D4 through D6 retain separate physical objects with empty annotation memberships. The strict reader uses the two typed active parameters and all four dormant parameter/cache states. It derives the D3 witness pair, framed display and ordinary zero anchor from the original sketch corner and signed pitch.
- The ordinary SDK exposes an editable `LinearPattern` with the real seed and support plane as its inputs. Both read modes retain parameter identities, signed direction, selected configuration, body topology and the six recorded driver roles. A full read includes the reconstructed single closed body. The design-only read omits the boundary while retaining the same editable neutral graph.
- The separate principal read status keeps the measured oblique republication predicate scoped to its existing state. The output carries no persisted kernel ID and claims no writer qualification. The public write entry refuses all four readbacks in both modes, leaving its supplied sink and cursor unchanged. Ordinary oblique scope and existing exact artifacts remain independently verified. [Read state](../../../src/convert/adapters/solidworks/Core/TypedResolved/Patterns/PatEvidence.py)

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePrincipalPatternRead.py \
  --origin /absolute/generated/origin/initial \
  --placed /absolute/generated/placed > /tmp/PrincipalPatternColdRead.json
```

The parent matches each file to the prior archive proof. Each guarded child calls normal `open_document` on both the named input path and an in-memory stream with full and design-only options. The detached neutral JSON checks retain both interpretations. Each case checks all 24 distinct physical display, handle, dimension and parameter objects, exact typed value and display cache for all six roles, actual catalogue IDs and the two active neutral provenance bindings. The solid comparison checks paired edge incidence, exact topology counts and independently expected volume, area, centroid and bounds. Path reads permit only the supplied input. Stream reading, neutral JSON and writer refusal perform zero file reads after module initialization.

| Generated control | Count | Pitch in mm | Solid faces |
| --- | ---: | ---: | ---: |
| Origin Right | 3 | 31.875 | 21 |
| Origin Top | 5 | 19.75 | 31 |
| Placed Right | 3 | 27.183 | 21 |
| Placed Top | 4 | 25.163 | 26 |

The four cases complete 16 normal strict opens. Format inference and full reading open only the designated native path in each path run. Existing oblique comparisons reproduce both whole-file hashes via 40 authored and readback publications and preserve all 96 refusals. [Oblique guard](../../tooling/sw2026/linear_pattern/neutral/VerifyMeasuredPattern.py)

Five model-only contrasts change a named annotation frame, the active pitch view, a dormant view, the pitch witness or the selected datum line. Each refuses full strict reconstruction. Its design-only fallback carries generic history without the typed principal result. No vendor process runs, and no additional native or held-out acceptance is claimed. [Guarded receipt](../measurements/2026/LocalPrincipalPatternColdRead01.json)
