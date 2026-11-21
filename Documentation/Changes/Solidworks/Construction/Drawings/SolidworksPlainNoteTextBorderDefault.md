# Plain drawing note text border default

The internal plain-note constructor now initializes the separate text-border
switch alongside the inherited text parser flags. Exact 2026 SP05.2 code
binds this setting to the concrete generic text constructor and its separate
border lookup. A plain note still has only the authored text and computed
line and character owners. It does not acquire a border.

The guarded comparison changes one Definition byte and no other logical
stream for the same authored input. Its re-read retains the same map and
exact text, with zero writer input reads. See the
[constructor evidence](../../../../../re/solidworks/records/DrawingPlainNoteTextBorder2026.md)
and [guarded receipt](../../../../../re/solidworks/measurements/2026/DrawingPlainNoteTextBorder01.json).
Rendered note acceptance and public admission remain open.
