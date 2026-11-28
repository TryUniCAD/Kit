# Named constraint text needs actual owner IDs

Both disclosed FCStd sources contain a live expression while their portable `Expression.parameter_ids` are empty. One names an actual spreadsheet alias; the other names the real sketch-width constraint from Pad.Length. Cached numbers still make the same present solid, so geometry-only checks cannot expose the missing dependency ownership.

Resolve the actual native object, named constraint or cell address/alias, parameter owner and raw expression-engine path before evaluating arithmetic. Preserve the source text and all metadata. Add only existing qualified parameter IDs to a reader projection; a sheet cell is not an existing Parameter and must keep its full owner semantics. Reject stale cached values, duplicate aliases and foreign owner paths. The [two-source ledger](../../../../../re/solidworks/records/FcstdRectangleSourceOwners2026.md) retains those boundaries and emits no stripped native part.
