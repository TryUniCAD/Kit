# Explicit empty part text requires its own streams

An empty dictionary can represent an authored scope or the absence of a
scope. The local import model emits no XML for the latter. A generated
compatible `Contents/CusProps` manager alone reports property compatibility
without creating the summary, document or configuration dictionaries on
readback.

Retain model presence for each authored empty scope and emit its own
ordinary XML stream using the shared text serializer. Configuration text
still requires the selected native configuration's owner.
[Measured scope comparison](../../../../../../re/solidworks/records/ImportedEmptyPartText2026.md)
