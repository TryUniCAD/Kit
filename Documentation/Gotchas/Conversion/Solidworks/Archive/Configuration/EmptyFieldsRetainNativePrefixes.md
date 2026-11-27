# Empty fields can retain native prefixes

A density-unit presence byte can be nonzero and still introduce a
null object tag. Keep an explicit presence byte and its actual node
field together when re-emitting a typed archive. A fresh graph can
derive presence from its modeled node when it supplies no byte.

A negative signed length for an ordinary positive repeat can yield
zero rows. Preserve a stored word that still describes those rows.
Derive the count when the row inventory changes. The separate bounded
atom-manager writer continues to derive its count from actual atoms.

The complete Config-0 process checks presence with null and concrete
nodes, negative lengths in empty repeats, and a fresh length after
changing the rows. The independently authored field changes load
through the same typed archive code as the unchanged native controls.
[Measured archive variants](../../../../../../re/solidworks/records/OrdinaryPartConfigGraph2026.md#retained-wire-forms)
