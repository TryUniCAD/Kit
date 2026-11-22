# Read a cold SOLIDWORKS rotated three-mate assembly

Strict SDK inspection now reads the ordinary version-19000 cold assembly
profile with an ordered parallel, distance and coincident mate group.
It follows both occurrences to their actual shared cold part, recovers the
six datum endpoints and binds the live driving distance. The default
geometry read also returns the linked rectangular child's solid.
`include_brep=False` retains the same mate graph and editable parameters.

When component resolution is disabled, the reader returns both occurrences
and defers the typed mate graph. The three-mate inspection scope is
separate from the measured two-mate writer. Saved warm assemblies continue
through their existing reader path.
[Process verification](../../../../re/solidworks/measurements/2026/ColdRotatedMateRead01.json)

The complete suite builds a second assembly and its linked part from a fresh
neutral recipe in an isolated process. It checks the full and design-only
readers, relative companion resolution, the deferred route, and strict refusal
of a separately generated group with a different ordered mate layout.
[Complete-suite case](../../../../tests/Convert/Solidworks/PlanarWriting/ColdRotatedMateTests.py)
