# Kernel traversal order differs from file order

Parasolid's ordinary body APIs do not enumerate edges by first face/fin encounter or by their transmit-record positions. The pinned implementation first uses the body's direct edge chain, then walks region and shell edge chains. Face enumeration walks region and shell primary face chains. Its direct body-shell and parallel front-face pointers have different roles.

Use the actual typed head/next ownership graph and preserve one allocation history. Do not sort native tags, use a portable edge suffix, or deduplicate a face walk to invent downstream IDs. A valid graph traversal does not yet prove the modelling operation's initial link order or native acceptance of a generated cache.

[Exact runtime fields, native API ranges and disclosed counterexamples](../../../../../../re/solidworks/records/ParasolidBodyTraversal2026.md)
