# Bounded XY dual-side live identity rules

Recorded before production validator implementation. The inspected source is PR #394's committed `TwoSidedDraft20261127` native campaign, not generated output. `Discovery.json` binds all 48 non-holdout XY drafted archives by SHA-256 and records every actual live attribute, class inventory, selected curve tag and active operation sequence. The six XY `holdout_b` archives are withheld from this rule derivation; their later evaluation must not change a failed rule without recording a separate revision. Earlier geometry work had already measured their numerical controls, so this is a tag-specific holdout, not a wholly unseen model lineage.

No new wire grammar is proposed. Existing typed codecs parse these fields. The rule is a bounded semantic admission contract, supported by actual independently edited and restored source files and the earlier native campaign observations. It is not target conversion or writer acceptance. Models and native API calls remain off.

## Proposed contract and confidence

| Subject | Derived rule | Current confidence |
| --- | --- | --- |
| Active body and selected history | Source serializer key, `DcBody`/`Body` UUID and current body tag agree; the journal's current/max/initial states match feature start/end; feature ID maps are reciprocal | Existing `CheckSpanStore`, `ReadSpanOps`, `ReadSpanProgen` all pass the 48 discovery files |
| Allocated versus active operations | Derive active order from the body progenitor occurrence map, after validating the complete allocator. Require exactly two distinct active operations for the two geometrically separate sides; do not hardcode IDs | Confirmed for these discovery states; existing allocated/inactive distinction is retained |
| Body tag | One group names the first active operation with empty operation list and exact body-progenitor secondary tag | Confirmed discovery; existing body/progenitor join is reused |
| Side faces | Classify by independently checked cone axis: along normal uses active operation zero, against normal uses operation one. Both primary labels derive from the selected circle's curve progenitor | Confirmed discovery; angular sign never selects side ownership |
| Caps and far rims | Physical lower and upper cap labels are `1` and `2`; both far rim labels are `-1`. All bind the first active operation | Confirmed discovery and the established circular label vocabulary; current native IDs are never copied as constants |
| Profile joint edge | Exactly two groups, negative selected curve tag then positive selected curve tag, both on first active operation; all secondary and approach IDs zero | Confirmed discovery; requires held-out and encoded wrong-group counterexamples |
| Sketch attributes | Exactly two source links on the partnered joint coedges at the profile plane, selected circle tag, direction zero, secondary zero and unsplit flags | Confirmed discovery; reuse `CheckSpanLink` after proving physical joint ownership |
| Time attribute | Exactly one finite nonnegative microsecond timestamp, owned by the same body as its body tag | Confirmed discovery; timestamp value remains source data, never a rule constant |
| Attribute chains | Each geometry owner exposes a unique chain; every next/prior link and owner is reciprocal, no cycle, no attribute shared or unaccounted | Required independent validation; numeric record locations are not used |
| Complete live inventory | One root/body/lump/shell; four faces, six single-circle loops/coedges, three edges/vertices/points/ellipse carriers, two cones, two planes, eight feature tags, two sketch tags and one timestamp | Counts derive from the closed two-frustum topology; confirmed discovery, no unsupported extra attribute may be silently retained |

Before reading labels, the validator must verify the actual side/cap/rim carriers against the profile and independently varied distances/angles, full circle seams and reciprocal topology. A plausible primary label on a different physical owner must refuse. Normalization may only resolve journal aliases after every live reference is proved; it must not drop unknown records or attributes.

## Boundary and tests to perform

Only identity XY and a profile-plane two-sided circular NewBody graph are eligible. Both side distances are positive, the two side slopes remain distinct and all end radii positive. Existing untapered controls retain their old reader route; twelve XZ drafted states must continue to refuse this validator. The complete public source reader, parameter permission, saved snapshots, scene/material checks and dispatch remain owned separately by the root and snapshot worker.

Evaluate all 48 discovery files and six held-out XY files without changing the frozen rule. Preserve healthy controls' existing strict outcomes. Construct counterexamples by modifying typed source models and re-emitting actual archives: wrong operation or owner, stale body secondary ID, missing/swapped joint group, wrong side/cap/far label, incorrect selected circle, sketch source on another rim, extra/incorrect attribute ownership and broken reciprocal allocator/progenitor entries. A counterexample must fail at real archive decoding or at the new strict validator, never count as accepted from an isolated check alone.
