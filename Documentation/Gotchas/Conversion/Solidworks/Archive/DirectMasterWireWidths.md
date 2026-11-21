# An empty direct master uses canonical wire widths

The shared archive reader can decode a null from a six-byte tag. Its
writer encodes the typed null in two bytes because the tag model has
no source width. The shared count reader represents an extended
zero count with a width field, even though the collection is empty.

The measured direct master uses two-byte null tags and a two-byte
empty count in the inherited resolved list. Enable the graph
reader's canonical tag rule at the bounded master entry and reject
retained count width separately from a populated list. This keeps
the accepted master round trip exact and identifies each failure at
its own wire boundary.
[Guarded width contrasts](../../../../../re/solidworks/measurements/2026/ConfigSheetMetalBody02.json)
