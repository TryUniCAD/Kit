# Make automated reviews easier to scan

Published reviews lead with the actual native verdict, a soundness score out of five and explicit coverage.
The model's summary follows, then findings grouped in P1, P2 and P3 order.
Each finding has a title, a clickable code location bound to the reviewed revision, and an explanation.
Empty priority groups are omitted; a report without findings says so without claiming complete coverage.

Revision, scope, approval conditions, model configuration, trusted policy and CI evidence appear in a collapsible verification table.
Exact generated-source reconstruction is identified when present.
This changes presentation only; model scoring, finding validation, approval policy and lifecycle reactions retain their existing behavior.
The verdict comes from the trusted publisher's decision and cannot be selected by model text.
Text sanitization still prevents notifications and executable Markdown constructs.

The final mention and review-snapshot receipt lines retain their exact existing syntax and order.
They remain outside the collapsible block because scheduled request and approval receipt discovery depend on them.
See the [receipt-format gotcha](../../Gotchas/Review/ReviewReceiptMarkers.md).

AGENTS.md and the canonical skill require the same report structure.
Scope `ReviewerPresentation`, parent `ReviewerHosted`, owner `jdharcourt`, branch `fix/reviewer-live-acceptance-20261128`, delivery [PR #408](https://github.com/TryUniCAD/Kit/pull/408), remains active in the [owning register](../../Planning/Links.json).
Static Python and formatting verification and a real-report rendering inspection are recorded before publication; hosted presentation acceptance remains pending protected deployment.
This formatting change makes no new model-review, approval, parent-completion or CAD acceptance claim.
