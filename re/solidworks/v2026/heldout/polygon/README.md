# Locked polygon sources

`Lock.json` identifies three SOLIDWORKS 2026 SP05.2 polygon extrusions and two
separately saved rectangular controls. The application authored them from neutral
specifications before implementation of the polygon family emitter. Constructor
and archive helpers already existed; no generated polygon file was available.

The raw files remain in the private research store named by the lock. Their
SHA-256 values are immutable source identities. Writer authors must not inspect
their streams, fit fields to them, or use their saved values as defaults. The
neutral specifications and expected geometry may be used as conversion inputs.

All five authoring operations saved successfully with one solid body, and the
before/after controls have matching measured volume, surface area and centre of
mass. These are source measurements, not acceptance of generated output. The
original feature-error queries failed because the harness passed an integer
reference to a Boolean parameter. Consequently this lock does not establish
zero feature errors or warnings. Generated output still needs the full fresh
process, control, rebuild, dimension edit and save/reopen procedure.

The family emitter must derive its objects from format knowledge and neutral
input. These files are neither donor inputs nor runtime resources.
