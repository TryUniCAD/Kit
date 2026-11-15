# SOLIDWORKS 2026 profile construction helpers

The research builder constructs fresh polygon profile graphs from semantic vertices and constructor-backed format rules
Endpoint and handle indexes derive from node references when the archive schema reads the fields
The helpers contain no saved-record defaults or runtime file reads

Use `re/tooling/sw2026/builders/Sketch.py` with `re/tooling/sw2026` and its `serial` directory on the Python import path
All helper inputs are keyword-only
`ordinary_point` constructs a positioned ordinary 2D point
`ordinary_line` constructs an ordinary line from point nodes
`line_handle` refers to a line node in its owning array
`PlaneFrame` and `frame_transform` convert an authored orthogonal frame to native transform fields
`new_sketch` constructs native empty sketch collections and managers
`new_profile` binds that empty sketch to an already allocated profile feature and a plane-reference node
`closed_profile` adds a validated closed ring with any number of at least three vertices
`NodeOrder` keeps geometry references symbolic and computes its index map once when emission reads a field
Counts derive from the current collections

`Extrude.py` constructs native blind end specifications from four supplied live display-dimension nodes
It connects an allocated extrusion body feature to its profile
It checks the authored depth against its driving length parameter
The complete display-dimension factory remains unresolved
Missing model handles or driving parameters cause explicit construction errors

These helpers are intermediate research
The vertex-only profile contract contains no authored sketch dimensions or constraints
It does not preserve a source sketch that contains additional design intent
The helpers do not yet produce a complete live extrusion from scalar depth alone
They do not change adapter capabilities
See [the construction evidence](../../../re/solidworks/records/ProfileConstruction2026.md) for binary addresses, confidence labels, contracts, and remaining fields
The [instruction-boundary gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/DisassemblyEntryPoints.md) records a disassembly failure found during this work

No local tests or oracle measurements were run
The Python source passed static AST syntax parsing without imports or execution
Remote CI remains pending
Held-out native acceptance, rebuild, body measurements, and dimension edits remain unverified
