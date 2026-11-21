# Probe SOLIDWORKS through-all selection with two stock bodies

The disclosed Windows probe authors two separate stocks and one
through-all cut, with automatic or explicit scope. An edit of the
moving stock's live D1 brings it into the existing cut. Independent
volume, area, centre and extrema distinguish the intact stock from
the stock with a notch. Separate processes handle geometry and
rolled-back scope inspection.

The initial explicit call reached the cut command and returned null
between healthy controls. The automatic retry creates the cut and
passes its 48 initial geometry checks. Its direct scope query reports
a count of `-1` and an absent body array. The retry stopped before
the resulting scope could be qualified. The separate geometry and
scope protocol remains under native evaluation.
[Procedure and failure receipts](../../../../../re/solidworks/records/ThroughAllMultiStockScope2026.md)
