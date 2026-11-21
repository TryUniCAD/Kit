# Stock depths use the actual end slot

A builder's graph attaches an `owner` field to its depth display,
handle, dimension and parameter. The two measured cold two-stock
archives reconstruct those four nodes without the builder-side owner
fields. The generated dimension's `retaining_handles` tuple is also
an in-memory annotation in this path. Both stocks use the displayed
name `D1`.

Follow each stock's actual `f818.f18` display pointer through the
local handle and dimension to its mapped length parameter. Validate
the identity of all nodes and keep the two dimension IDs distinct.
The original name or repeated `D1` text cannot identify the owner by
itself.
[Observed chain and contrasts](../../../../../../re/solidworks/records/TwoStockColdOwnershipRead2026.md)
