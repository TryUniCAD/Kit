# Required native-state transform for distance edits

The reconstruction receipt is for unchanged source semantics. Replacing only a neutral `Parameter.value` cannot produce a valid edited archive: the current writer checks equality with its typed-state projection. Replacing only the native `Parameter` and `DcDoubleParameter` copies likewise leaves the journal, snapshot and mass cache inconsistent. Removing either equality check is not a solution.

For the bounded identity-XY full-circle, untapered extent family, a future edit transform has the following exact semantic input/output contract. This is a required-work description, not an implemented transform or an acceptance claim.

## Inputs and extent evaluation

Inputs are the already qualified source graph, the actual `DistanceExtrude` definition and one independently edited length parameter, with its existing owner and role retained. A two-sided extrusion requires two distinct positive distance parameters. The circular profile radius and XY center stay unchanged. No OffsetStart, taper, extra feature or occurrence-frame change is admitted in this increment.

Let `a` be the actual first distance, `b` the optional second distance and `o=0`, in millimeters. The evaluated stations are:

| Side mode | Lower `l` | Upper `u` |
| --- | --- | --- |
| one-sided | `min(0,a)` | `max(0,a)` |
| two-sided | `-b` | `a` |
| symmetric full | `-a/2` | `a/2` |
| symmetric per side | `-a` | `a` |

Use the existing `GetDistValues`/`GetDistSpan` evaluator, including finite, noncollapsed and positive-magnitude requirements. Do not normalize away a reverse extent's negative driving value. A symmetric second taper can alias the first taper by its existing documented rule; two-sided first and second driver identities remain distinct.

## Native changes that must be performed together

1. Resolve the edited neutral identity to its existing `Parameter` and reciprocal owned `DcDoubleParameter`, through the actual feature reference (`rAlongDistance`/selected Along binding or `rAgainstDistance`). Convert millimeters to internal centimeters, update both numeric copies, and regenerate a literal or preserve a supported user-parameter reference with consistent dependency values. Keep names, units, owner, parent, reciprocal binding, allocator ID and every unchanged parameter intact. Preserve the supported negative literal expression convention.
2. Rebuild the solved body in **every affected journal state** using the derived radius, center and new stations. A correct final body alone is insufficient. Preserve the state/operation/progenitor ownership graph and the source's active versus allocated operation distinction. Update all affected cap planes, circular boundary curves, vertices, edge intervals/closed seams, cylinder carrier placement and physical feature tags; validate the full live table and coverage. A single global Z translation or scale is insufficient because the profile/sketch sheets stay at Z=0 while the two physical ends move independently.
3. Rebuild the final saved solid snapshot and its separate sketch/profile sheets with matching identities. `CheckSpanSave` checks the unique solid, both circular sheets, every carrier and complete physical label coverage independently from the active history. Sheet labels cannot substitute for physical cap labels.
4. Recompute the native body cache from the new cylinder: height `h=u-l`, volume `pi*r*r*h`, area `2*pi*r*(r+h)`, center `(cx,cy,(l+u)/2)` and the complete origin-frame inertia tensor, including off-diagonal parallel-axis terms. Internal values use centimeters. The existing `RotaryMass` formulas and cache-only tolerances define the check; stale component/body overrides remain forbidden.
5. Rebuild all affected graphics geometry, tessellation and bounds from the edited analytic shape. Preserve scene ownership, materials, appearance and all unaffected fields. Retaining source graphics whose end station still describes the old solid would violate losslessness even if a native recompute repairs the display. Identify and implement this typed graphics derivation rather than copying one candidate's vertices.
6. Independently emit complete Design/ACT/Browser segments, body journals, snapshot, graphics, materials and all required auxiliary members from the coherent typed model. Recompute framing, lengths, record indexes and archive bookkeeping through existing emitters. No byte-offset patch, saved payload replacement or fixture table is permitted.
7. Read the emitted archive through the ordinary strict reader and compare it with the independently rebuilt edited neutral graph, including unchanged source semantics and the changed parameter role, complete geometry, timeline and material graph. Reject before destination mutation if either graph differs. Typed self-equality alone is insufficient.

## Required proof before promotion

Use independent edits of the actual first and second distance where present, negative one-sided distances, both symmetric conventions, and held-out center/radius/distance combinations. Preserve expected rejected edits (zero/negative two-sided magnitude, nonfinite, wrong owner, inconsistent expression, unsupported start/frame/taper) with existing destination bytes intact.

The root-owned oracle must open the new candidate bytes before recompute, compare control/candidate geometry and feature/parameter inventories, rebuild, edit each driver independently, restore it, save and reopen the edit and restoration in a fresh process, and bracket the run with healthy controls. Save-after-edit bytes must also pass strict reader comparison. A native edit of an unchanged reconstructed file demonstrates native parametric usability; it does not prove that Kit generated a changed neutral graph.

Source-free authoring for this family is a separate extension. Existing `DocumentSpec.Features` / `ExtrudeSpec` can construct some symmetric/two-sided solids, but their generic part neutral steps are not the reference-driven native span graph and do not establish lossless source conversion. The authored solver must supply all required histories, bindings and exact neutral semantics before that route can close this gap.
