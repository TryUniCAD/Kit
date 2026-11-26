# Prepare logical input for a saved P03 constrained Boss

Use this research procedure to check the pinned positive XY SOLIDWORKS P03 baseline, then replay its constrained rectangle through the existing logical Boss constructor.
The operation checks the original strict reader output against the discovery archive and independent reopen receipt. It checks the Boss's saved profile reference and the matching sketch and feature owner spans.

## Run the procedure

Run each command with the repository's Python 3.14 developer dependencies and unused paths.

```sh
python -I -B re/automation/P03ConstraintIntent.py capture --output /private/p03-source.json
python -I -B re/automation/P03ConstraintIntent.py prepare --input /private/p03-source.json --output /private/p03-logical.json
python -I -B re/automation/P03ConstraintIntent.py replay --input /private/p03-logical.json
```

Keep the original `capture` JSON and the `prepare` report together. The report binds the original archive SHA-256, source JSON SHA-256, prepared JSON SHA-256, selected feature, sketch, support and Origin identities. `replay` reads only the prepared logical model. It reports its dimensions, parameter owners, point slots and ordered constraints. Replay alone cannot authenticate the original source.

## Scope

The four line-axis rules target the four selected perimeter lines. Width binds the bottom edge from its start to its end. Height binds the left edge from its end to its start. The Origin coincidence binds a distinct saved external point to the first local corner. The four inferred corner joins certify shared point aliases. They do not add four saved solver relations. Target allocation still belongs to the existing deterministic constructor.

This discovery procedure handles one baseline with one active Front Plane sketch and its first positive blind Boss. Its original Join is recorded separately from the constructor's first-body Create intent. The logical input has no retained record bytes. Keep the original with its twenty-five native feature definitions and other state outside this projection. No native candidate is emitted. Public conversion, whole-source preservation, held-out generalization and licensed edit and reopen acceptance remain open. See [the owning register](../../../Reference/Research/AutomationSteps.md#a12-solidworks-writer-research) and [the paired archive evidence](../Readers/Comparison/RectangularPairEvidence.md).

## Verification

The source capture comes from revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Its exact native SHA-256 is `db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357`. Both native owners point to the 6,437-byte record beginning at offset 5,578. The logical model keeps ordered 40 mm width and 20 mm height operands and the linked 10 mm depth. The strict archived input exposes seven saved relations and four inferred joins.

The Windows Python 3.14.6 process case passed in 50.64 seconds. A separate process reopened the prepared JSON after the test moved the supplied source JSON away. It reproduced the ordered references, two driving side lengths, the distinct Origin and the exact logical report. A same-length opposite edge, reversed height operands, a local point substituted for Origin and a shifted owner span each refused before publishing. Both an existing destination and an output path equal to the original source preserved their prior bytes.

See [rectangle height operand side](../../../Gotchas/Research/Readers/ConstrainedBoss/RectangleHeightOperandSide.md) for the same-length wrong-edge refusal.

The final review follow-up passed the process case in 61.40 seconds on Windows Python 3.14.6. It asserts the exact four H/V targets and refuses a change outside the projection when it reaches the pinned-source comparison. The CI rationale checker reproduced the same eight violations on the unmodified PR #168 base `e2fba13c8f`. Six comment wording corrections and two missing lambda comments in the inherited tests preserve their Python syntax trees and all assertions.

The dependent base skipped three Python checks that the current CI aggregate requires on pull requests. The existing [prequeue Python check conditions](https://github.com/TryUniCAD/Kit/pull/224/files) restore Python steering, Pyright and Mypy on pull requests and merge-group candidates.

The phase map lists all three Python checks in both phases. The aggregate excludes only jobs unique to the other phase from its required result. The existing process cases exercise skipped required Python checks and legitimately deferred research compatibility.
