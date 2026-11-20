# Neutral SDK preparation for a two-stock selected circular cut

This is the staged neutral writer slice of `B04-SW2026-EXTRUDE-THROUGHALL` for PR #121. The assembly frontier lane owns preparation and guarded process evidence. The programme owner controls the pre-writer source locks, the SOLIDWORKS 2026 SP05.2 oracle and final admission. The source dependencies are the [two-stock owner construction](TwoStockColdOwnerGraph2026.md), the [strict cache-free reader](TwoStockColdSdkRead2026.md) and the common SDK part archive builder. The new writer uses the same typed constructors for the part environment, archive headers, class maps, sketches and dimensions.

## Exact neutral boundary

One ordinary Default configuration and millimetre geometry describe two disjoint rectangular prisms. The first is on the positive canonical Front plane and the second on the positive canonical Right plane. Each profile owns four closed lines and their driving axis relations. Each blind boss owns its separate positive `D1`. The free closed circle uses the actual Front support and an explicit historical body selection reached through the first feature. Its effective direction is positive Front, with either a complete interior tunnel or a proper exterior notch on one side. A coincident unextended circle centre point may accompany the circle. The resulting body list orders the untouched Right solid ahead of the cut result, each with the label of its producing feature.

The planner refuses document and feature extensions, saved geometry and provenance, other configurations, unsupported names, extra or crossed driver ownership, alternate supports, undeclared selection metadata and conflicting output identities. The selection label must be the implicit stock label or the implicit label derived from its actual producer. The two original volumes must have positive separation. Geometry is checked by the same analytic constructors used by the strict reader before the writer allocates its native graph.

The first stock uses `moExtrusion_c` with operation `f810=-1`. The independent second stock uses `moICE_c` with `f810=0` and keeps the common boss flags and live blind end display. Both receive distinct generated atom entries allocated in operation order. Each entry links the actual producer, its manager membership and its own output alias. The cutter uses `moICE_c` operation `f810=1`, its own depthless through end and one `moCompSolidBody_c` selection bound to the Front producer and its atom. The cut-result and chooser records are left for native regeneration. No kernel IDs or physical cache records are inferred. Keyword rows are constructed from the same actual root and feature identities, two owned driver displays and their sketch children.

## Frozen evaluator entry

`convert.adapters.solidworks.Core.Preparation.TwoStock.PlanTwoStocks.PlanTwoStocks(document)` validates the neutral request. For an immutable destination the evaluator can use the corresponding complete preparation entry.

```python
from io import BytesIO

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
    PrepareStockPart,
)

candidate = PrepareStockPart(
    document,
    BytesIO(),
    written_at,
    WriteOptions(values={"final_destination": final_windows_part}),
)
payload = candidate.BytesValue
```

The generated stream dictionary is also available as `candidate.StreamsValue`. The call does not write to its target. The evaluator owns transport and all filesystem writes. An eventual public route can use the same exact planner for eligibility and pass the returned archive from `PrepareStockPart` to the existing destination writer without changing any generation behavior. Public eligibility remains closed in this revision.

## Guarded host proof

```sh
python3.14 -IB re/tooling/sw2026/throughsource/twostockgraph/ProveSdkStockWriter.py
```

The supervisor launches 14 isolated host processes and records the baseline revision. Model creation, archive construction and strict readback run behind the process audit guard. An independent invocation of the earlier research composer receives the same disclosed authored inputs and explicit event. No vendor artifact or source lock payload enters either writer. The receipt records all generated stream hashes, code hashes and the refusal messages.

| Request | Result | Checks |
| --- | --- | --- |
| Disclosed Front notch | 8,574 bytes and ten streams | Entire container SHA-256 `6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508` equals the prior native-tested generated archive. Both D1s, the explicit selected owner, all 23 ordered public tree rows and two analytic solids survive strict readback. |
| Independent enclosed circle | 8,845 bytes and ten streams | The measured body volumes are 4,908.75 and 5,099.557559909952 mm³. Analytic area and centre checks agree for both solids, which have six and seven faces. Authored names and changed shape values vary generated stream lengths. |
| Unrepresented inputs | Eleven refusals | Metadata and feature extensions, foreign stock selection, custom body label, mismatched D1, extended support, inactive naming scope, reserved root name, tangent circle and wrong or missing target. |

All guarded workers report zero runtime access attempts. This tranche launched no SOLIDWORKS process and examined no private source or specification. The prior [disclosed native run](../measurements/2026/TwoStockColdNative01.json) remains the authority for the exact reproduced bytes on build `34.5.2.0604`. Public admission requires prospective locked native source comparison through the actual selected ownership, both editable stock drivers, measured geometry, save and fresh reopen between healthy controls. Arbitrary saved presentation, automatic enrolment and other stock/datum combinations require separate coverage.
