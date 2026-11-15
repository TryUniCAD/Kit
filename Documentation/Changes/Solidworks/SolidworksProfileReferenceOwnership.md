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
Remote results and controlled native measurements remain pending.
This repair does not establish generated-part acceptance or enable the production writer.

The [ownership gotcha](../../Gotchas/Conversion/Solidworks/Model/PlaneReferencesOwnTheirComponents.md) describes the required lifetime relationships.
