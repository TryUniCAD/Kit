# Separate references in fresh part composition

The research part composer now creates separate plane references for the origin and ordinary sketch.
Each reference owns its own unit-component copy.
Both copies retain the same model owner and reference the same principal plane.

The native profile setter adopts its supplied reference.
Replacing that reference deletes the previous allocation directly.
Sharing one reference between profiles therefore gives that allocation two exclusive owners.
The [native ownership record](../../../re/solidworks/records/ModelConstruction2026.md#plane-wrappers) documents the constructor and deletion paths.

The complete-file subprocess check decodes both configuration and resolved streams with their shared archive map.
Its report requires separate reference and component allocations, the same plane identity, and the same actual model owner.
Construction and decoding remain inside the existing file-access and process-launch denial boundary.
No local tests were run.
The complete-file process check passed in [remote run 43706398170](https://github.com/TryUniCAD/Kit/actions/runs/43706398170), job `132788308932`, at `f374f83195eeeb32536db7ef8ba50ca61b094d47`.
The enclosing PR revision failed strict typing on the new research-schema imports, repaired separately.
The [controlled native inspection](../../../re/solidworks/measurements/2026/FreshPartProfileOwnership.json) still rejected the generated candidate between two healthy original controls.
The candidate SHA-256 was `3b68ad9e4d77c180b02cb59423aaa25be1d8b560d03b23470347055ffa03f03d`.
This repair does not establish generated-part acceptance or enable the production writer.

The [ownership gotcha](../../Gotchas/Conversion/Solidworks/Model/PlaneReferencesOwnTheirComponents.md) describes the required lifetime relationships.
