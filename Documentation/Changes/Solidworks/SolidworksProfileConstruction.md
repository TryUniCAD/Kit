# SOLIDWORKS 2026 profile construction helpers

The research builder gains constructor-backed point, line, visibility, and plane-frame helpers
Endpoint and handle indexes derive from node references when the archive schema reads the fields
The helpers contain no saved-record defaults or runtime file reads

Use `re/tooling/sw2026/builders/Sketch.py` with the `serial` directory on the Python import path
All helper inputs are keyword-only
`ordinary_point` constructs a positioned ordinary 2D point
`ordinary_line` constructs an ordinary line from point nodes
`line_handle` refers to a line node in its owning array
`PlaneFrame` and `frame_transform` convert an authored orthogonal frame to native transform fields
`new_sketch` constructs native empty sketch collections and managers
`new_profile` binds that empty sketch to an already allocated profile feature and a plane-reference node

These helpers are intermediate research
They do not yet build a complete dimensioned sketch, profile, or extrusion
They do not change adapter capabilities
See [the construction evidence](../../../re/solidworks/records/ProfileConstruction2026.md) for binary addresses, confidence labels, contracts, and remaining fields
The [instruction-boundary gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/DisassemblyEntryPoints.md) records a disassembly failure found during this work

No local tests or oracle measurements were run
The Python source passed static AST syntax parsing without imports or execution
Remote CI remains pending
Held-out native acceptance, rebuild, body measurements, and dimension edits remain unverified
